from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from api.dependencies import (
    get_git_service, 
    get_llm_service, 
    get_repository,
    get_analysis,
    get_report,
    repositories_db,
    analyses_db,
    reports_db,
    generate_id
)
from models.repository import Repository, RepositoryStatus
from models.analysis import Analysis, AnalysisStatus
from models.report import Report, ReportSummary
from core.code_analysis import run_analysis
from core.report_generator import generate_report

router = APIRouter()

class AnalysisCreate(BaseModel):
    repository_id: str

class AnalysisResponse(BaseModel):
    id: str
    repository_id: str
    status: AnalysisStatus

async def process_analysis(
    analysis_id: str, 
    repository_id: str,
    git_service,
    llm_service
):
    """Background task to perform code analysis"""
    try:
        # Update analysis status to in progress
        analyses_db[analysis_id]["status"] = AnalysisStatus.IN_PROGRESS
        
        # Get repository data
        repo_data = repositories_db.get(repository_id)
        if not repo_data:
            analyses_db[analysis_id]["status"] = AnalysisStatus.FAILED
            analyses_db[analysis_id]["error"] = f"Repository {repository_id} not found"
            return
            
        repository = Repository(**repo_data)
        
        # Run the analysis
        analysis_result = await run_analysis(repository, git_service, llm_service)
        
        # Store results
        analysis_result.id = analysis_id
        analyses_db[analysis_id] = analysis_result.dict()
        
        # Generate report
        report_id = generate_id("report-")
        report = await generate_report(analysis_result, repository)
        report.id = report_id
        reports_db[report_id] = report.dict()
        
        # Link report ID to analysis
        analyses_db[analysis_id]["report_id"] = report_id
        analyses_db[analysis_id]["status"] = AnalysisStatus.COMPLETED
        
    except Exception as e:
        # Update status to failed in case of error
        if analysis_id in analyses_db:
            analyses_db[analysis_id]["status"] = AnalysisStatus.FAILED
            analyses_db[analysis_id]["error"] = str(e)
        print(f"Error analyzing repository: {str(e)}")

@router.post("/", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(
    analysis_data: AnalysisCreate,
    background_tasks: BackgroundTasks,
    git_service = Depends(get_git_service),
    llm_service = Depends(get_llm_service)
):
    """Start analysis on a repository"""
    repository_id = analysis_data.repository_id
    
    # Check if repository exists
    if repository_id not in repositories_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository with ID {repository_id} not found"
        )
    
    # Create analysis entry
    analysis_id = generate_id("analysis-")
    analysis = Analysis(
        id=analysis_id,
        repository_id=repository_id,
        status=AnalysisStatus.PENDING
    )
    
    analyses_db[analysis_id] = analysis.dict()
    
    # Schedule background task
    background_tasks.add_task(
        process_analysis,
        analysis_id,
        repository_id,
        git_service,
        llm_service
    )
    
    return analyses_db[analysis_id]

@router.get("/{analysis_id}", response_model=Analysis)
async def get_analysis_status(analysis_id: str):
    """Get analysis status and results"""
    return get_analysis(analysis_id)

@router.get("/{analysis_id}/report", response_model=Report)
async def get_analysis_report(analysis_id: str):
    """Get the report for an analysis"""
    analysis = get_analysis(analysis_id)
    
    if analysis["status"] != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report not available yet for analysis {analysis_id}"
        )
    
    report_id = analysis.get("report_id")
    if not report_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No report found for analysis {analysis_id}"
        )
    
    return get_report(report_id)
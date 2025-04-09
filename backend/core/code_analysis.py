import asyncio
from typing import Dict, List, Any, Optional

from models.repository import Repository
from models.analysis import Analysis, AnalysisStatus, StructuralAnalysis
from services.gitingest_service import GitIngestService
from services.llm_service import LLMService
from core.repo_ingestion import collect_files_for_analysis, extract_language_stats
from agents.structural_analyzer import analyze_repository_structure
from agents.pattern_recognizer import identify_patterns
from agents.smell_detector import detect_smells
from agents.refactoring_advisor import suggest_refactorings

async def run_analysis(
    repository: Repository, 
    git_service: GitIngestService,
    llm_service: LLMService
) -> Analysis:
    """Orchestrate the full code analysis process"""
    
    # Initialize analysis
    analysis = Analysis(
        id="temp",  # Will be replaced by the caller
        repository_id=repository.id,
        status=AnalysisStatus.IN_PROGRESS
    )
    
    try:
        # Step 1: Collect files for analysis
        files_content = await collect_files_for_analysis(repository, git_service)
        if not files_content:
            analysis.status = AnalysisStatus.FAILED
            analysis.error = "No analyzable files found in repository"
            return analysis
        
        # Step 2: Structural analysis
        structural_analysis = await analyze_repository_structure(repository, files_content)
        analysis.structural_analysis = structural_analysis
        
        # Step 3: Run pattern recognition
        design_patterns = await identify_patterns(files_content, llm_service)
        analysis.design_patterns = design_patterns
        
        # Step 4: Detect code smells (analyze files in parallel)
        code_smells = []
        smell_tasks = []
        for file_path, content in files_content.items():
            smell_tasks.append(detect_smells(file_path, content, llm_service))
        
        # Gather smell detection results
        smell_results = await asyncio.gather(*smell_tasks)
        for result in smell_results:
            code_smells.extend(result)
        
        analysis.code_smells = code_smells
        
        # Step 5: Suggest refactorings based on code smells
        refactoring_suggestions = await suggest_refactorings(code_smells, files_content, llm_service)
        analysis.refactoring_suggestions = refactoring_suggestions
        
        # Update status
        analysis.status = AnalysisStatus.COMPLETED
        
    except Exception as e:
        analysis.status = AnalysisStatus.FAILED
        analysis.error = str(e)
    
    return analysis
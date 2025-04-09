from fastapi import Depends, HTTPException, status
from typing import Dict, Any, Optional
import uuid

from services.gitingest_service import GitIngestService
from services.llm_service import LLMService
from config.settings import settings

# In-memory storage for development
# In production, this should be replaced with a proper database
repositories_db: Dict[str, Dict[str, Any]] = {}
analyses_db: Dict[str, Dict[str, Any]] = {}
reports_db: Dict[str, Dict[str, Any]] = {}

def get_git_service() -> GitIngestService:
    return GitIngestService()

def get_llm_service() -> LLMService:
    return LLMService()

def get_repository(repo_id: str) -> Dict[str, Any]:
    if repo_id not in repositories_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository with ID {repo_id} not found"
        )
    return repositories_db[repo_id]

def get_analysis(analysis_id: str) -> Dict[str, Any]:
    if analysis_id not in analyses_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID {analysis_id} not found"
        )
    return analyses_db[analysis_id]

def get_report(report_id: str) -> Dict[str, Any]:
    if report_id not in reports_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found"
        )
    return reports_db[report_id]

def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with an optional prefix"""
    return f"{prefix}{uuid.uuid4()}"
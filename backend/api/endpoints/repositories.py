from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional

from services.gitingest_service import GitIngestService
from api.dependencies import get_git_service, get_repository, repositories_db, generate_id
from models.repository import Repository, RepositoryStatus

router = APIRouter()

class RepositoryCreate(BaseModel):
    url: HttpUrl
    branch: str = "main"

class RepositoryResponse(BaseModel):
    id: str
    url: HttpUrl
    branch: str
    status: RepositoryStatus
    
    class Config:
        schema_extra = {
            "example": {
                "id": "repo-123",
                "url": "https://github.com/username/repo",
                "branch": "main",
                "status": "pending"
            }
        }

async def process_repository(repo_id: str, repo_url: str, branch: str, git_service: GitIngestService):
    """Background task to clone and process repository"""
    try:
        repository = await git_service.clone_repository(repo_url, branch)
        repository.id = repo_id  # Use the pre-generated ID
        repositories_db[repo_id] = repository.dict()
    except Exception as e:
        # Update status to failed in case of error
        if repo_id in repositories_db:
            repositories_db[repo_id]["status"] = RepositoryStatus.FAILED
            repositories_db[repo_id]["error"] = str(e)
        print(f"Error processing repository: {str(e)}")

@router.post("/", response_model=RepositoryResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_repository(
    repo_data: RepositoryCreate,
    background_tasks: BackgroundTasks,
    git_service: GitIngestService = Depends(get_git_service)
):
    """Submit a repository for analysis"""
    repo_id = generate_id("repo-")
    
    # Create initial repository entry
    initial_repo = Repository(
        id=repo_id,
        url=repo_data.url,
        branch=repo_data.branch,
        status=RepositoryStatus.PENDING
    )
    
    repositories_db[repo_id] = initial_repo.dict()
    
    # Schedule background task to clone and process
    background_tasks.add_task(
        process_repository,
        repo_id,
        str(repo_data.url),
        repo_data.branch,
        git_service
    )
    
    return repositories_db[repo_id]

@router.get("/{repo_id}", response_model=Repository)
async def get_repository_status(repo_id: str):
    """Get repository status and information"""
    return get_repository(repo_id)

@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repo_id: str,
    git_service: GitIngestService = Depends(get_git_service)
):
    """Delete a repository and its cloned data"""
    repo = get_repository(repo_id)
    repo_obj = Repository(**repo)
    
    # Clean up the cloned repository
    if repo_obj.clone_path:
        await git_service.cleanup_repository(repo_obj)
    
    # Remove from in-memory storage
    repositories_db.pop(repo_id, None)
    
    return None
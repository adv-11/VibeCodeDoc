from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class RepositoryStatus(str, Enum):
    PENDING = "pending"
    CLONING = "cloning"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"

class FileInfo(BaseModel):
    path: str
    size: int
    extension: str
    content: Optional[str] = None

class Directory(BaseModel):
    path: str
    files: List[FileInfo] = []
    subdirectories: List['Directory'] = []

class Repository(BaseModel):
    id: str
    url: HttpUrl
    branch: str = "main"
    status: RepositoryStatus = RepositoryStatus.PENDING
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    clone_path: Optional[str] = None
    structure: Optional[Directory] = None
    metadata: Dict[str, any] = {}
    error: Optional[str] = None
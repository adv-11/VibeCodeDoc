import os
import shutil
import uuid
from git import Repo
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from config.settings import settings
from models.repository import Repository, Directory, FileInfo, RepositoryStatus

class GitIngestService:
    def __init__(self, base_dir: str = settings.REPO_CLONE_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
    
    async def clone_repository(self, repo_url: str, branch: str = "main") -> Repository:
        """Clone a git repository and return a Repository object"""
        repo_id = str(uuid.uuid4())
        clone_path = os.path.join(self.base_dir, repo_id)
        
        repository = Repository(
            id=repo_id,
            url=repo_url,
            branch=branch,
            status=RepositoryStatus.CLONING,
            clone_path=clone_path
        )
        
        try:
            # Clone the repository
            Repo.clone_from(repo_url, clone_path, branch=branch)
            repository.status = RepositoryStatus.PENDING
            repository.structure = await self.analyze_directory_structure(clone_path)
            return repository
        except Exception as e:
            repository.status = RepositoryStatus.FAILED
            repository.error = str(e)
            # Clean up failed clone
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            raise e
    
    async def analyze_directory_structure(self, dir_path: str, rel_path: str = "") -> Directory:
        """Recursively analyze directory structure"""
        abs_path = os.path.join(dir_path, rel_path)
        directory = Directory(path=rel_path or "/")
        
        # Skip .git directory
        if ".git" in abs_path:
            return directory
        
        for item in os.listdir(abs_path):
            item_rel_path = os.path.join(rel_path, item)
            item_abs_path = os.path.join(abs_path, item)
            
            # Skip hidden files and directories
            if item.startswith('.'):
                continue
                
            if os.path.isfile(item_abs_path):
                # Check file size to avoid very large files
                file_size = os.path.getsize(item_abs_path)
                if file_size <= settings.MAX_FILE_SIZE_KB * 1024:
                    file_info = FileInfo(
                        path=item_rel_path,
                        size=file_size,
                        extension=os.path.splitext(item)[1],
                    )
                    directory.files.append(file_info)
            elif os.path.isdir(item_abs_path):
                subdir = await self.analyze_directory_structure(dir_path, item_rel_path)
                directory.subdirectories.append(subdir)
        
        return directory
    
    async def get_file_content(self, repository: Repository, file_path: str) -> Optional[str]:
        """Get content of a file in the repository"""
        if not repository.clone_path:
            return None
            
        full_path = os.path.join(repository.clone_path, file_path)
        
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return None
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            # For binary files or encoding issues, return None
            return None
    
    async def cleanup_repository(self, repository: Repository) -> bool:
        """Remove cloned repository directory"""
        if repository.clone_path and os.path.exists(repository.clone_path):
            try:
                shutil.rmtree(repository.clone_path)
                return True
            except Exception:
                return False
        return False
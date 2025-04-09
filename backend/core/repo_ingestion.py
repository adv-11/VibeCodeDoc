import os
import logging
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
import base64
from urllib.parse import urlparse
import json

from config.settings import settings
from models.repository import Repository, RepositoryFile, RepositoryStructure

logger = logging.getLogger(__name__)

class RepositoryIngestionManager:
    """Manages the ingestion of code repositories for analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.github_token = settings.GITHUB_TOKEN
        self.max_file_size_kb = settings.MAX_FILE_SIZE_KB
        self.max_files = settings.MAX_FILES_PER_REPO
        self.supported_extensions = settings.SUPPORTED_EXTENSIONS
    
    async def ingest_repository(self, repo_url: str) -> Repository:
        """Ingest a repository from GitHub or local path"""
        try:
            # Parse the URL to determine the source
            parsed_url = urlparse(repo_url)
            
            if parsed_url.netloc == "github.com":
                # GitHub repository
                return await self._ingest_github_repository(repo_url)
            elif not parsed_url.netloc and os.path.exists(repo_url):
                # Local repository
                return await self._ingest_local_repository(repo_url)
            else:
                raise ValueError(f"Unsupported repository URL: {repo_url}")
                
        except Exception as e:
            self.logger.exception(f"Error ingesting repository {repo_url}: {str(e)}")
            raise
    
    async def _ingest_github_repository(self, github_url: str) -> Repository:
        """Ingest a repository from GitHub"""
        try:
            # Extract owner and repo name from GitHub URL
            # Example: https://github.com/owner/repo
            parts = github_url.rstrip('/').split('/')
            owner = parts[-2]
            repo_name = parts[-1]
            
            # Prepare API URL
            api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
            headers = {"Accept": "application/vnd.github.v3+json"}
            
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
            
            # Get repository metadata
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to fetch repository: {response.status}")
                    
                    repo_data = await response.json()
                
                # Get repository contents (file structure)
                structure = await self._fetch_github_repo_structure(session, owner, repo_name, headers)
                
                # Get file contents (limited by max_files)
                files = await self._fetch_github_files(session, owner, repo_name, headers, structure)
                
                return Repository(
                    name=repo_name,
                    owner=owner,
                    url=github_url,
                    description=repo_data.get("description", ""),
                    language=repo_data.get("language", ""),
                    stars=repo_data.get("stargazers_count", 0),
                    forks=repo_data.get("forks_count", 0),
                    files=files,
                    structure=structure
                )
                
        except Exception as e:
            self.logger.exception(f"Error ingesting GitHub repository {github_url}: {str(e)}")
            raise
    
    async def _fetch_github_repo_structure(self, session: aiohttp.ClientSession, 
                                         owner: str, repo: str, 
                                         headers: Dict, 
                                         path: str = "") -> RepositoryStructure:
        """Recursively fetch the repository structure from GitHub"""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise ValueError(f"Failed to fetch repo structure: {response.status}")
            
            contents = await response.json()
            
            structure = {}
            
            for item in contents:
                if item["type"] == "dir":
                    # Recursively process subdirectories
                    subdir_path = f"{path}/{item['name']}" if path else item["name"]
                    structure[item["name"]] = await self._fetch_github_repo_structure(
                        session, owner, repo, headers, subdir_path
                    )
                else:
                    # Only track supported file types
                    _, ext = os.path.splitext(item["name"])
                    if ext.lower() in self.supported_extensions:
                        structure[item["name"]] = {
                            "type": "file",
                            "size": item["size"],
                            "path": item["path"]
                        }
            
            return structure
    
    async def _fetch_github_files(self, session: aiohttp.ClientSession, 
                                owner: str, repo: str, 
                                headers: Dict, 
                                structure: Dict) -> List[RepositoryFile]:
        """Fetch file contents from GitHub repository"""
        # Flatten the structure to get all file paths
        files = []
        
        def extract_files(struct, current_path=""):
            for name, data in struct.items():
                if isinstance(data, dict) and "type" not in data:
                    # This is a directory
                    new_path = f"{current_path}/{name}" if current_path else name
                    extract_files(data, new_path)
                elif isinstance(data, dict) and data.get("type") == "file":
                    # This is a file
                    file_path = data.get("path", f"{current_path}/{name}" if current_path else name)
                    files.append({"path": file_path, "size": data.get("size", 0)})
        
        extract_files(structure)
        
        # Sort files by size (smallest first) and limit to max_files
        files.sort(key=lambda x: x["size"])
        files = files[:self.max_files]
        
        # Fetch file contents
        result = []
        
        for file_info in files:
            file_path = file_info["path"]
            
            # Skip files that are too large
            if file_info["size"] > self.max_file_size_kb * 1024:
                self.logger.warning(f"Skipping large file: {file_path} ({file_info['size']} bytes)")
                continue
            
            # Skip files with unsupported extensions
            _, ext = os.path.splitext(file_path)
            if ext.lower() not in self.supported_extensions:
                continue
            
            try:
                url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        self.logger.warning(f"Failed to fetch file {file_path}: {response.status}")
                        continue
                    
                    file_data = await response.json()
                    
                    # GitHub API returns content as base64 encoded
                    if file_data.get("encoding") == "base64":
                        content = base64.b64decode(file_data["content"]).decode("utf-8", errors="replace")
                        
                        result.append(RepositoryFile(
                            path=file_path,
                            name=os.path.basename(file_path),
                            extension=ext.lower(),
                            size=file_info["size"],
                            content=content
                        ))
                    
            except Exception as e:
                self.logger.exception(f"Error fetching file {file_path}: {str(e)}")
                continue
        
        return result
    
    async def _ingest_local_repository(self, local_path: str) -> Repository:
        """Ingest a repository from a local directory"""
        try:
            # Validate the path
            if not os.path.isdir(local_path):
                raise ValueError(f"Path is not a directory: {local_path}")
            
            # Get repository name from directory name
            repo_name = os.path.basename(os.path.abspath(local_path))
            
            # Collect repository structure
            structure = self._build_local_structure(local_path)
            
            # Collect files
            files = await self._collect_local_files(local_path, structure)
            
            # Determine primary language based on file extensions
            language_counts = {}
            for file in files:
                ext = file.extension.lower()
                language_counts[ext] = language_counts.get(ext, 0) + 1
            
            primary_language = max(language_counts.items(), key=lambda x: x[1])[0] if language_counts else ""
            
            return Repository(
                name=repo_name,
                owner="local",
                url=f"file://{os.path.abspath(local_path)}",
                description="Local repository",
                language=primary_language.lstrip('.'),
                stars=0,
                forks=0,
                files=files,
                structure=structure
            )
                
        except Exception as e:
            self.logger.exception(f"Error ingesting local repository {local_path}: {str(e)}")
            raise
    
    def _build_local_structure(self, path: str, relative_path: str = "") -> Dict:
        """Build a dictionary representing the local repository structure"""
        structure = {}
        
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            rel_path = os.path.join(relative_path, item) if relative_path else item
            
            # Skip hidden files and directories
            if item.startswith('.'):
                continue
            
            if os.path.isdir(full_path):
                # Process subdirectory
                structure[item] = self._build_local_structure(full_path, rel_path)
            else:
                # Process file
                _, ext = os.path.splitext(item)
                if ext.lower() in self.supported_extensions:
                    file_size = os.path.getsize(full_path)
                    structure[item] = {
                        "type": "file",
                        "size": file_size,
                        "path": rel_path
                    }
        
        return structure
    
    async def _collect_local_files(self, base_path: str, structure: Dict) -> List[RepositoryFile]:
        """Collect files from a local repository"""
        files = []
        
        def extract_files(struct, current_path=""):
            for name, data in struct.items():
                if isinstance(data, dict) and "type" not in data:
                    # This is a directory
                    new_path = os.path.join(current_path, name) if current_path else name
                    extract_files(data, new_path)
                elif isinstance(data, dict) and data.get("type") == "file":
                    # This is a file
                    file_path = data.get("path", os.path.join(current_path, name) if current_path else name)
                    files.append({
                        "path": file_path, 
                        "size": data.get("size", 0),
                        "full_path": os.path.join(base_path, file_path)
                    })
        
        extract_files(structure)
        
        # Sort files by size (smallest first) and limit to max_files
        files.sort(key=lambda x: x["size"])
        files = files[:self.max_files]
        
        # Read file contents
        result = []
        
        for file_info in files:
            file_path = file_info["path"]
            full_path = file_info["full_path"]
            
            # Skip files that are too large
            if file_info["size"] > self.max_file_size_kb * 1024:
                self.logger.warning(f"Skipping large file: {file_path} ({file_info['size']} bytes)")
                continue
            
            # Skip files with unsupported extensions
            _, ext = os.path.splitext(file_path)
            if ext.lower() not in self.supported_extensions:
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    
                    result.append(RepositoryFile(
                        path=file_path,
                        name=os.path.basename(file_path),
                        extension=ext.lower(),
                        size=file_info["size"],
                        content=content
                    ))
                    
            except Exception as e:
                self.logger.exception(f"Error reading file {file_path}: {str(e)}")
                continue
        
        return result

# Create an instance to be imported by other modules
repo_ingestion = RepositoryIngestionManager()
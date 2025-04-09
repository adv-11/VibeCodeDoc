import httpx
import logging
from config.settings import settings
from bs4 import BeautifulSoup
import re
import os
import tempfile
import subprocess
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class GitIngestService:
    """Service to fetch repository contents using GitIngest or direct Git clone."""
    
    def __init__(self):
        self.base_url = settings.GITINGEST_BASE_URL
        self.headers = {
            "User-Agent": "Code-Analysis-System/1.0"
        }
    
    async def fetch_repository(self, repo_url: str) -> Dict:
        """Fetch repository content using GitIngest"""
        try:
            # Convert GitHub URL to GitIngest URL
            if "github.com" in repo_url:
                ingested_url = repo_url.replace("github.com", "gitingest.com")
            else:
                ingested_url = f"{self.base_url}/{repo_url}"
            
            logger.info(f"Fetching repo from: {ingested_url}")
            
            async with httpx.AsyncClient(headers=self.headers) as client:
                response = await client.get(ingested_url, timeout=60.0)
                
            if response.status_code != 200:
                logger.error(f"Failed to fetch repo: {response.status_code}")
                return {"status": "error", "message": f"Failed to fetch repository: {response.status_code}"}
                
            # Parse the GitIngest response
            return self._parse_gitingest_response(response.text, repo_url)
            
        except Exception as e:
            logger.exception(f"Error fetching repository: {str(e)}")
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def _parse_gitingest_response(self, html_content: str, repo_url: str) -> Dict:
        """Parse the GitIngest HTML response to extract repository structure and file contents"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract repo metadata
        repo_name = repo_url.split('/')[-1]
        owner = repo_url.split('/')[-2] if len(repo_url.split('/')) > 4 else "unknown"
        
        # Extract files from the page
        files = []
        file_divs = soup.find_all('div', class_='file-content')
        
        for div in file_divs:
            file_path = div.get('data-path', '')
            if not file_path:
                continue
                
            file_content = div.text.strip()
            
            files.append({
                "path": file_path,
                "content": file_content,
                "size": len(file_content),
                "extension": os.path.splitext(file_path)[1][1:] if '.' in file_path else ""
            })
        
        # Construct directory structure
        structure = self._build_directory_structure(files)
        
        return {
            "status": "success",
            "repository": {
                "name": repo_name,
                "owner": owner,
                "url": repo_url,
            },
            "structure": structure,
            "files": files
        }
    
    def _build_directory_structure(self, files: List[Dict]) -> Dict:
        """Build a tree representation of the directory structure"""
        root = {"name": "/", "type": "directory", "children": {}}
        
        for file in files:
            path_parts = file["path"].split('/')
            current = root
            
            # Navigate through directories
            for i, part in enumerate(path_parts):
                if i == len(path_parts) - 1:  # This is a file
                    if "files" not in current:
                        current["files"] = []
                    current["files"].append({
                        "name": part,
                        "path": file["path"],
                        "extension": file["extension"]
                    })
                else:  # This is a directory
                    if part not in current["children"]:
                        current["children"][part] = {
                            "name": part, 
                            "type": "directory", 
                            "children": {}
                        }
                    current = current["children"][part]
        
        return self._flatten_structure(root)
    
    def _flatten_structure(self, node: Dict) -> Dict:
        """Convert the nested dictionary structure to a more front-end friendly format"""
        result = {
            "name": node["name"],
            "type": node["type"],
            "children": []
        }
        
        # Add files to children
        if "files" in node:
            for file in node["files"]:
                result["children"].append({
                    "name": file["name"],
                    "type": "file",
                    "path": file["path"],
                    "extension": file["extension"],
                })
        
        # Process subdirectories
        if "children" in node and isinstance(node["children"], dict):
            for child_name, child_node in node["children"].items():
                result["children"].append(self._flatten_structure(child_node))
        
        return result
    
    async def clone_repository(self, repo_url: str) -> Optional[str]:
        """Alternative method: Clone the repository to a temporary directory"""
        try:
            temp_dir = tempfile.mkdtemp()
            
            # Clone the repo
            process = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, temp_dir],
                check=True,
                capture_output=True,
                text=True
            )
            
            return temp_dir
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e.stderr}")
            return None
        except Exception as e:
            logger.exception(f"Repository cloning failed: {str(e)}")
            return None

# Instance to be imported by other modules
gitingest_service = GitIngestService()
import os
from typing import Dict, List, Optional, Set

from models.repository import Repository, FileInfo
from services.gitingest_service import GitIngestService
from config.settings import settings

async def collect_files_for_analysis(repository: Repository, git_service: GitIngestService) -> Dict[str, str]:
    """Collect files from the repository for analysis"""
    result = {}
    
    if not repository.structure:
        return result
    
    # Get list of files to analyze
    files_to_analyze = await _list_analyzable_files(repository.structure)
    
    # Limit the number of files to avoid overwhelming the system
    files_to_analyze = files_to_analyze[:settings.MAX_FILES_TO_ANALYZE]
    
    # Get content for each file
    for file_info in files_to_analyze:
        content = await git_service.get_file_content(repository, file_info.path)
        if content:
            result[file_info.path] = content
    
    return result

async def _list_analyzable_files(directory, file_list=None, extensions=None) -> List[FileInfo]:
    """Recursively list all analyzable files in the repository"""
    if file_list is None:
        file_list = []
    
    # Common code file extensions to analyze
    if extensions is None:
        extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.cs', 
            '.go', '.rb', '.php', '.swift', '.kt', '.rs', '.scala', '.html', '.css'
        }
    
    # Add files in current directory
    for file_info in directory.files:
        if any(file_info.path.endswith(ext) for ext in extensions):
            file_list.append(file_info)
    
    # Recursively process subdirectories
    for subdir in directory.subdirectories:
        await _list_analyzable_files(subdir, file_list, extensions)
    
    return file_list

async def extract_language_stats(repository: Repository) -> Dict[str, float]:
    """Extract stats about programming languages used in the repository"""
    if not repository.structure:
        return {}
    
    # Count files by extension
    extension_counts = {}
    
    def count_extensions(directory):
        for file_info in directory.files:
            ext = os.path.splitext(file_info.path)[1].lower()
            if ext:
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        for subdir in directory.subdirectories:
            count_extensions(subdir)
    
    count_extensions(repository.structure)
    
    # Map extensions to languages
    extension_to_language = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript (React)',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript (React)',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.cs': 'C#',
        '.go': 'Go',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.rs': 'Rust',
        '.scala': 'Scala',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sh': 'Shell',
        '.md': 'Markdown',
        '.json': 'JSON',
        '.xml': 'XML',
        '.yaml': 'YAML',
        '.yml': 'YAML',
    }
    
    # Aggregate by language
    language_counts = {}
    for ext, count in extension_counts.items():
        language = extension_to_language.get(ext, 'Other')
        language_counts[language] = language_counts.get(language, 0) + count
    
    # Convert to percentages
    total_files = sum(language_counts.values())
    if total_files == 0:
        return {}
    
    language_percentages = {
        lang: round(count / total_files * 100, 1)
        for lang, count in language_counts.items()
    }
    
    # Sort by percentage descending
    return dict(sorted(language_percentages.items(), key=lambda x: x[1], reverse=True))
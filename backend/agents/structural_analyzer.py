import logging
from typing import Dict, List, Any
import os
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

class StructuralAnalyzer:
    """Agent responsible for analyzing the structural aspects of a codebase"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def analyze_structure(self, repository: Dict) -> Dict:
        """Analyze the repository structure"""
        try:
            # Get structure analysis from LLM
            structure_analysis = await llm_service.analyze_repository_structure(repository)
            
            if structure_analysis["status"] != "success":
                self.logger.error(f"Structure analysis failed: {structure_analysis['message']}")
                return structure_analysis
            
            # Enhance with language statistics
            structure_analysis["data"]["language_statistics"] = self._calculate_language_statistics(repository)
            
            # Analyze file distribution
            structure_analysis["data"]["file_distribution"] = self._analyze_file_distribution(repository)
            
            return structure_analysis
            
        except Exception as e:
            self.logger.exception(f"Error in structural analysis: {str(e)}")
            return {
                "status": "error",
                "message": f"Error in structural analysis: {str(e)}"
            }
    
    def _calculate_language_statistics(self, repository: Dict) -> Dict:
        """Calculate statistics about programming languages used in the repository"""
        language_counts = {}
        language_bytes = {}
        total_bytes = 0
        
        # Map of file extensions to languages
        ext_to_language = {
            "py": "Python",
            "js": "JavaScript",
            "ts": "TypeScript",
            "jsx": "React JSX",
            "tsx": "React TSX",
            "java": "Java",
            "c": "C",
            "cpp": "C++",
            "h": "C/C++ Header",
            "hpp": "C++ Header",
            "cs": "C#",
            "go": "Go",
            "rb": "Ruby",
            "php": "PHP",
            "swift": "Swift",
            "kt": "Kotlin",
            "rs": "Rust",
            "html": "HTML",
            "css": "CSS",
            "scss": "SCSS",
            "sass": "Sass",
            "less": "Less",
            "json": "JSON",
            "xml": "XML",
            "yaml": "YAML",
            "yml": "YAML",
            "md": "Markdown",
            "txt": "Plain Text",
            "sh": "Shell",
            "bat": "Batch",
            "ps1": "PowerShell",
            "sql": "SQL",
            "r": "R",
            "m": "Objective-C",
            "mm": "Objective-C++",
            "dart": "Dart",
            "lua": "Lua",
            "pl": "Perl",
            "pm": "Perl",
            "scala": "Scala",
            "clj": "Clojure",
            "ex": "Elixir",
            "exs": "Elixir",
            "hs": "Haskell",
            "erl": "Erlang",
            "fs": "F#",
            "fsx": "F#",
            "vue": "Vue",
            "svelte": "Svelte",
        }
        
        for file in repository["files"]:
            # Get extension without leading dot
            ext = file.get("extension", "").lower()
            
            # Determine language based on extension
            language = ext_to_language.get(ext, "Other")
            
            # Update counts
            language_counts[language] = language_counts.get(language, 0) + 1
            
            # Update bytes
            file_size = file.get("size", 0)
            language_bytes[language] = language_bytes.get(language, 0) + file_size
            total_bytes += file_size
        
        # Calculate percentages
        language_percentages = {}
        for lang, bytes_count in language_bytes.items():
            if total_bytes > 0:
                language_percentages[lang] = round((bytes_count / total_bytes) * 100, 2)
            else:
                language_percentages[lang] = 0
        
        return {
            "language_counts": language_counts,
            "language_bytes": language_bytes,
            "language_percentages": language_percentages,
            "total_files": len(repository["files"]),
            "total_bytes": total_bytes,
            "primary_language": max(language_counts.items(), key=lambda x: x[1])[0] if language_counts else "Unknown"
        }
    
    def _analyze_file_distribution(self, repository: Dict) -> Dict:
        """Analyze how files are distributed across the repository"""
        # Count files per directory
        dir_counts = {}
        
        for file in repository["files"]:
            path = file.get("path", "")
            directory = os.path.dirname(path)
            
            if not directory:
                directory = "/"
            
            dir_counts[directory] = dir_counts.get(directory, 0) + 1
        
        # Get directories with the most files
        top_directories = sorted(dir_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Calculate directory depth statistics
        depths = [len(path.split("/")) - 1 for path in dir_counts.keys()]
        avg_depth = sum(depths) / len(depths) if depths else 0
        max_depth = max(depths) if depths else 0
        
        return {
            "directory_count": len(dir_counts),
            "top_directories": top_directories,
            "average_directory_depth": avg_depth,
            "maximum_directory_depth": max_depth
        }

# Instance to be imported by other modules
structural_analyzer = StructuralAnalyzer()
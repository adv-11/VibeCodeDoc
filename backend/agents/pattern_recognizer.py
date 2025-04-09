import logging
from typing import Dict, List, Any
import re
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

class PatternRecognizer:
    """Agent responsible for recognizing design patterns in code"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define pattern signatures for quick pre-screening
        self.pattern_signatures = {
            "Singleton": {
                "indicators": [
                    r"private\s+static\s+\w+\s+instance",
                    r"private\s+\w+\(\)",
                    r"getInstance\(\)",
                    r"@Singleton",
                    r"static\s+\w+\s+instance",
                    r"if\s*\(\s*instance\s*==\s*null\s*\)",
                ],
                "languages": ["Java", "C#", "C++", "Python", "TypeScript", "JavaScript"],
            },
            "Factory": {
                "indicators": [
                    r"create\w+",
                    r"factory",
                    r"getInstance",
                    r"new\s+\w+\(",
                    r"return\s+new\s+\w+",
                ],
                "languages": ["Java", "C#", "C++", "Python", "TypeScript", "JavaScript"],
            },
            "Observer": {
                "indicators": [
                    r"addObserver|subscribe|attach",
                    r"removeObserver|unsubscribe|detach",
                    r"notify\w*",
                    r"update\(",
                    r"@Subscribe",
                    r"EventEmitter",
                ],
                "languages": ["Java", "C#", "C++", "Python", "TypeScript", "JavaScript"],
            },
            "Strategy": {
                "indicators": [
                    r"interface\s+\w+Strategy",
                    r"class\s+\w+Strategy",
                    r"setStrategy",
                    r"strategy\.",
                ],
                "languages": ["Java", "C#", "C++", "Python", "TypeScript", "JavaScript"],
            },
            "Decorator": {
                "indicators": [
                    r"@\w+",
                    r"wrap\w*",
                    r"decorate",
                    r"class\s+\w+Decorator",
                ],
                "languages": ["Java", "C#", "C++", "Python", "TypeScript", "JavaScript"],
            },
            "MVC": {
                "indicators": [
                    r"class\s+\w+Controller",
                    r"class\s+\w+View",
                    r"class\s+\w+Model",
                    r"render\(",
                    r"@Controller",
                ],
                "languages": ["Java", "C#", "C++", "Python", "TypeScript", "JavaScript"],
            },
        }
    
    async def analyze_file_patterns(self, file_path: str, file_content: str, repository_context: Dict) -> Dict:
        """Analyze a file for design patterns"""
        try:
            # Extract file extension
            file_ext = file_path.split(".")[-1].lower() if "." in file_path else ""
            
            # Pre-screen for potential patterns
            potential_patterns = self._pre_screen_patterns(file_content, file_ext)
            
            # If potential patterns found, send to LLM for detailed analysis
            if potential_patterns:
                # Add pattern context to repository context
                enhanced_context = repository_context.copy()
                enhanced_context["potential_patterns"] = potential_patterns
                
                # Get pattern analysis from LLM
                return await llm_service.analyze_file(file_path, file_content, enhanced_context)
            else:
                # No patterns pre-screened, still send to LLM but with lower expectation
                return await llm_service.analyze_file(file_path, file_content, repository_context)
            
        except Exception as e:
            self.logger.exception(f"Error in pattern recognition for {file_path}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error in pattern recognition: {str(e)}",
                "file_path": file_path
            }
    
    def _pre_screen_patterns(self, file_content: str, file_ext: str) -> List[str]:
        """Pre-screen file content for potential design patterns"""
        potential_patterns = []
        
        # Map file extension to language
        ext_to_language = {
            "py": "Python", 
            "js": "JavaScript", 
            "ts": "TypeScript",
            "jsx": "React JSX",
            "tsx": "React TSX",
            "java": "Java",
            "c": "C",
            "cpp": "C++",
            "cs": "C#",
            "go": "Go",
            "rb": "Ruby",
            "php": "PHP",
            # Add more languages as needed
        }
        
        file_language = ext_to_language.get(file_ext, "Unknown")
        
        # Check each pattern signature
        for pattern_name, pattern_info in self.pattern_signatures.items():
            # Skip if language isn't supported for this pattern
            if file_language not in pattern_info["languages"] and file_language != "Unknown":
                continue
                
            # Check pattern indicators
            match_count = 0
            for indicator in pattern_info["indicators"]:
                if re.search(indicator, file_content, re.IGNORECASE):
                    match_count += 1
            
            # If more than one indicator matches, consider it a potential pattern
            if match_count >= 1:
                potential_patterns.append(pattern_name)
        
        return potential_patterns

# Instance to be imported by other modules
pattern_recognizer = PatternRecognizer()
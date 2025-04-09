import logging
import asyncio
from typing import Dict, List, Any, Optional
import time

from config.settings import settings
from services.llm_service import llm_service
from agents.structural_analyzer import structural_analyzer
from agents.pattern_recognizer import pattern_recognizer
from agents.smell_detector import smell_detector
from agents.refactoring_advisor import refactoring_advisor
from models.repository import Repository
from models.analysis import FileAnalysis, RepositoryAnalysis

logger = logging.getLogger(__name__)

class CodeAnalysisManager:
    """Manages the code analysis process"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.max_parallel_analyses = settings.MAX_ANALYSIS_THREADS
    
    async def analyze_repository(self, repository: Repository) -> RepositoryAnalysis:
        """Analyze the entire repository"""
        try:
            start_time = time.time()
            
            # Store repository context for reference
            repository_context = {
                "name": repository.name,
                "owner": repository.owner,
                "url": repository.url,
                "language": repository.language
            }
            
            # Analyze repository structure
            self.logger.info(f"Analyzing structure of repository: {repository.name}")
            structure_analysis = await structural_analyzer.analyze_structure(repository.structure, repository_context)
            
            # Analyze individual files
            self.logger.info(f"Analyzing {len(repository.files)} files in repository: {repository.name}")
            file_analyses = await self._analyze_files(repository.files, repository_context)
            
            # Generate repository-level design pattern analysis
            pattern_analysis = await pattern_recognizer.analyze_repository_patterns(repository, file_analyses)
            
            # Generate final report
            self.logger.info(f"Generating final report for repository: {repository.name}")
            final_report = await llm_service.generate_final_report(
                repo_data={"repository": repository_context},
                file_analyses=[analysis.model_dump() for analysis in file_analyses],
                structure_analysis=structure_analysis
            )
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            return RepositoryAnalysis(
                repository=repository_context,
                structure_analysis=structure_analysis,
                file_analyses=file_analyses,
                pattern_analysis=pattern_analysis,
                final_report=final_report.get("data", {}),
                execution_time=execution_time
            )
            
        except Exception as e:
            self.logger.exception(f"Error analyzing repository {repository.name}: {str(e)}")
            raise
    
    async def _analyze_files(self, files: List[Any], repository_context: Dict) -> List[FileAnalysis]:
        """Analyze individual files in parallel"""
        
        async def analyze_file(file):
            try:
                # Perform initial LLM analysis
                llm_analysis = await llm_service.analyze_file(
                    file_path=file.path,
                    file_content=file.content,
                    repository_context=repository_context
                )
                
                # Detect code smells
                smells = await smell_detector.detect_smells(
                    file_path=file.path,
                    file_content=file.content,
                    llm_analysis=llm_analysis
                )
                
                # Detect design patterns
                patterns = await pattern_recognizer.detect_patterns(
                    file_path=file.path,
                    file_content=file.content,
                    llm_analysis=llm_analysis
                )
                
                # Generate refactoring suggestions
                refactoring = await refactoring_advisor.suggest_refactorings(
                    file_path=file.path,
                    file_content=file.content,
                    analysis_results=llm_analysis
                )
                
                # Generate refactoring guide
                refactoring_guide = await refactoring_advisor.generate_refactoring_guide(
                    file_path=file.path,
                    suggestions=refactoring.get("refactoring_suggestions", [])
                )
                
                return FileAnalysis(
                    file_path=file.path,
                    file_name=file.name,
                    file_extension=file.extension,
                    llm_analysis=llm_analysis.get("data", {}),
                    smells=smells.get("smells", []),
                    patterns=patterns.get("patterns", []),
                    refactoring_suggestions=refactoring.get("refactoring_suggestions", []),
                    refactoring_guide=refactoring_guide.get("guide", {})
                )
                
            except Exception as e:
                self.logger.exception(f"Error analyzing file {file.path}: {str(e)}")
                return FileAnalysis(
                    file_path=file.path,
                    file_name=file.name,
                    file_extension=file.extension,
                    error=str(e)
                )
        
        # Use a semaphore to limit concurrent tasks
        semaphore = asyncio.Semaphore(self.max_parallel_analyses)
        
        async def analyze_with_semaphore(file):
            async with semaphore:
                return await analyze_file(file)
        
        # Create tasks for all files
        tasks = [analyze_with_semaphore(file) for file in files]
        
        # Execute all tasks and collect results
        return await asyncio.gather(*tasks)
    
    async def analyze_single_file(self, file_content: str, file_name: str, language: str) -> Dict:
        """Analyze a single file without repository context"""
        try:
            # Determine file extension
            if "." in file_name:
                extension = "." + file_name.split(".")[-1].lower()
            else:
                extension = ""
            
            # Create minimal context
            context = {
                "name": "standalone_analysis",
                "owner": "user",
                "language": language
            }
            
            # Perform LLM analysis
            llm_analysis = await llm_service.analyze_file(
                file_path=file_name,
                file_content=file_content,
                repository_context=context
            )
            
            # Detect code smells
            smells = await smell_detector.detect_smells(
                file_path=file_name,
                file_content=file_content,
                llm_analysis=llm_analysis
            )
            
            # Detect design patterns
            patterns = await pattern_recognizer.detect_patterns(
                file_path=file_name,
                file_content=file_content,
                llm_analysis=llm_analysis
            )
            
            # Generate refactoring suggestions
            refactoring = await refactoring_advisor.suggest_refactorings(
                file_path=file_name,
                file_content=file_content,
                analysis_results=llm_analysis
            )
            
            # Generate refactoring guide
            refactoring_guide = await refactoring_advisor.generate_refactoring_guide(
                file_path=file_name,
                suggestions=refactoring.get("refactoring_suggestions", [])
            )
            
            return {
                "status": "success",
                "file_name": file_name,
                "language": language,
                "llm_analysis": llm_analysis.get("data", {}),
                "smells": smells.get("smells", []),
                "patterns": patterns.get("patterns", []),
                "refactoring_suggestions": refactoring.get("refactoring_suggestions", []),
                "refactoring_guide": refactoring_guide.get("guide", {})
            }
            
        except Exception as e:
            self.logger.exception(f"Error analyzing file {file_name}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error analyzing file: {str(e)}",
                "file_name": file_name
            }

# Create an instance to be imported by other modules
code_analysis_manager = CodeAnalysisManager()
from typing import Dict, List, Any
import os
import statistics

from models.repository import Repository
from models.analysis import StructuralAnalysis
from core.repo_ingestion import extract_language_stats

async def analyze_repository_structure(repository: Repository, files_content: Dict[str, str]) -> StructuralAnalysis:
    """Analyze the structural aspects of a repository"""
    
    # Count files and directories
    file_count = 0
    directory_set = set()
    
    for file_path in files_content.keys():
        file_count += 1
        # Add all parent directories to the set
        path_parts = file_path.split('/')
        for i in range(len(path_parts)):
            directory = '/'.join(path_parts[:i])
            if directory:
                directory_set.add(directory)
    
    directory_count = len(directory_set)
    
    # Calculate language breakdown
    language_breakdown = await extract_language_stats(repository)
    
    # Calculate complexity metrics
    complexity_metrics = await calculate_complexity_metrics(files_content)
    
    # Build dependency graph
    dependency_graph = await build_dependency_graph(files_content)
    
    return StructuralAnalysis(
        file_count=file_count,
        directory_count=directory_count,
        language_breakdown=language_breakdown,
        complexity_metrics=complexity_metrics,
        dependency_graph=dependency_graph
    )

async def calculate_complexity_metrics(files_content: Dict[str, str]) -> Dict[str, Any]:
    """Calculate complexity metrics for the codebase"""
    metrics = {
        "average_complexity": 0,
        "max_complexity": 0,
        "average_lines_per_file": 0,
        "max_lines": 0,
        "average_function_length": 0,
        "file_size_distribution": {}
    }
    
    # Calculate line counts
    line_counts = [len(content.split('\n')) for content in files_content.values()]
    
    if line_counts:
        metrics["average_lines_per_file"] = round(statistics.mean(line_counts), 1)
        metrics["max_lines"] = max(line_counts)
    
    # Simple complexity estimation based on code characteristics
    complexities = []
    for file_path, content in files_content.items():
        complexity = await estimate_file_complexity(file_path, content)
        complexities.append(complexity)
    
    if complexities:
        metrics["average_complexity"] = round(statistics.mean(complexities), 1)
        metrics["max_complexity"] = max(complexities)
    
    # File size distribution
    size_ranges = {"small": 0, "medium": 0, "large": 0, "very_large": 0}
    for content in files_content.values():
        lines = len(content.split('\n'))
        if lines < 100:
            size_ranges["small"] += 1
        elif lines < 300:
            size_ranges["medium"] += 1
        elif lines < 500:
            size_ranges["large"] += 1
        else:
            size_ranges["very_large"] += 1
    
    total_files = len(files_content)
    if total_files > 0:
        metrics["file_size_distribution"] = {
            k: round(v / total_files * 100, 1) for k, v in size_ranges.items()
        }
    
    return metrics

async def estimate_file_complexity(file_path: str, content: str) -> float:
    """Estimate complexity of a file based on characteristics"""
    lines = content.split('\n')
    extension = os.path.splitext(file_path)[1].lower()
    
    # Base complexity starts at 1.0
    complexity = 1.0
    
    # Factor 1: Line count
    line_count = len(lines)
    if line_count > 500:
        complexity += 3.0
    elif line_count > 300:
        complexity += 2.0
    elif line_count > 100:
        complexity += 1.0
    
    # Factor 2: Nesting level
    indentation_levels = []
    for line in lines:
        if line.strip() and not line.strip().startswith(('#', '//', '/*', '*')):
            indent = len(line) - len(line.lstrip())
            indentation_levels.append(indent)
    
    if indentation_levels:
        avg_indent = sum(indentation_levels) / len(indentation_levels)
        max_indent = max(indentation_levels) if indentation_levels else 0
        
        # More indentation means more complexity
        if max_indent > 20:
            complexity += 2.0
        elif max_indent > 12:
            complexity += 1.0
        
        if avg_indent > 8:
            complexity += 1.0
    
    # Factor 3: Language-specific complexity indicators
    if extension in ('.py', '.js', '.ts'):
        # Count conditional statements and loops
        control_keywords = ['if', 'for', 'while', 'switch', 'case']
        keyword_count = sum(line.strip().startswith(kw) for kw in control_keywords for line in lines)
        keyword_density = keyword_count / max(1, line_count)
        
        if keyword_density > 0.1:
            complexity += 1.0
    
    # Factor 4: Function/method count
    function_indicators = {
        '.py': ['def ', 'async def '],
        '.js': ['function ', 'const ', '=>'],
        '.ts': ['function ', 'const ', '=>'],
        '.java': ['public ', 'private ', 'protected ', 'void ', 'static '],
        '.c': [') {', ') {'],
        '.cpp': [') {', ') {'],
        '.cs': ['public ', 'private ', 'protected ', 'void ', 'static '],
    }
    
    indicators = function_indicators.get(extension, [') {'])
    function_count = sum(
        1 for line in lines 
        if any(indicator in line for indicator in indicators)
    )
    
    if function_count > 20:
        complexity += 2.0
    elif function_count > 10:
        complexity += 1.0
    
    # Cap complexity at 10
    return min(10.0, complexity)

async def build_dependency_graph(files_content: Dict[str, str]) -> Dict[str, List[str]]:
    """Build a basic dependency graph between files"""
    dependency_graph = {}
    file_basenames = {
        os.path.splitext(os.path.basename(path))[0]: path 
        for path in files_content.keys()
    }
    
    for file_path, content in files_content.items():
        dependencies = []
        
        # Look for import statements
        import_patterns = {
            '.py': ['import ', 'from '],
            '.js': ['import ', 'require('],
            '.ts': ['import ', 'require('],
            '.java': ['import '],
            '.cpp': ['#include '],
            '.c': ['#include '],
        }
        
        extension = os.path.splitext(file_path)[1]
        patterns = import_patterns.get(extension, [])
        
        # Simple heuristic detection of imports
        for line in content.split('\n'):
            line = line.strip()
            for pattern in patterns:
                if line.startswith(pattern):
                    # Extract the imported module name
                    parts = line.split()
                    if len(parts) > 1:
                        module_name = parts[1].strip('";\'')
                        # Check if this import refers to one of our files
                        base_module = module_name.split('.')[0].split('/')[0]
                        if base_module in file_basenames and file_basenames[base_module] != file_path:
                            dependencies.append(file_basenames[base_module])
        
        dependency_graph[file_path] = dependencies
    
    return dependency_graph
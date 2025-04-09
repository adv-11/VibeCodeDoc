from typing import Dict, List, Any
import os
import re

from models.analysis import DesignPattern
from services.llm_service import LLMService

async def identify_patterns(files_content: Dict[str, str], llm_service: LLMService) -> List[DesignPattern]:
    """Identify design patterns in the codebase using both heuristics and LLM"""
    patterns = []
    
    # Use heuristic detection first
    heuristic_patterns = await heuristic_pattern_detection(files_content)
    patterns.extend(heuristic_patterns)
    
    # Use LLM for more sophisticated pattern detection
    llm_patterns = await llm_pattern_detection(files_content, llm_service)
    
    # Merge and deduplicate patterns
    all_patterns = patterns + llm_patterns
    deduplicated_patterns = await deduplicate_patterns(all_patterns)
    
    return deduplicated_patterns

async def heuristic_pattern_detection(files_content: Dict[str, str]) -> List[DesignPattern]:
    """Use heuristics to detect common design patterns"""
    patterns = []
    
    # Check for singleton pattern
    singleton_files = []
    for file_path, content in files_content.items():
        if await detect_singleton(file_path, content):
            singleton_files.append(file_path)
    
    if singleton_files:
        patterns.append(DesignPattern(
            name="Singleton",
            files=singleton_files,
            confidence=0.8,
            description="The Singleton pattern ensures a class has only one instance and provides a global point of access to it."
        ))
    
    # Check for factory pattern
    factory_files = []
    for file_path, content in files_content.items():
        if await detect_factory(file_path, content):
            factory_files.append(file_path)
    
    if factory_files:
        patterns.append(DesignPattern(
            name="Factory",
            files=factory_files,
            confidence=0.7,
            description="The Factory pattern provides an interface for creating objects without specifying their concrete classes."
        ))
    
    # Check for observer pattern
    observer_files = []
    for file_path, content in files_content.items():
        if await detect_observer(file_path, content):
            observer_files.append(file_path)
    
    if observer_files:
        patterns.append(DesignPattern(
            name="Observer",
            files=observer_files,
            confidence=0.7,
            description="The Observer pattern defines a one-to-many dependency between objects so that when one object changes state, all its dependents are notified and updated automatically."
        ))
    
    return patterns

async def detect_singleton(file_path: str, content: str) -> bool:
    """Detect singleton pattern"""
    ext = os.path.splitext(file_path)[1].lower()
    
    # Python singleton detection
    if ext == '.py':
        has_instance_var = '_instance' in content or '__instance' in content
        has_get_instance = 'get_instance' in content or 'getInstance' in content
        return has_instance_var and has_get_instance
    
    # JavaScript/TypeScript singleton detection
    elif ext in ['.js', '.ts', '.jsx', '.tsx']:
        has_instance_var = 'this.instance' in content or 'this._instance' in content
        has_module_exports = 'module.exports' in content
        has_get_instance = 'getInstance' in content
        return (has_instance_var and has_get_instance) or (has_module_exports and 'new ' not in content)
    
    # Java/C# singleton detection
    elif ext in ['.java', '.cs']:
        has_private_constructor = 'private ' in content and ' new ' in content
        has_static_instance = 'static ' in content and 'getInstance' in content
        return has_private_constructor and has_static_instance
    
    return False

async def detect_factory(file_path: str, content: str) -> bool:
    """Detect factory pattern"""
    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path).lower()
    
    # Check filename
    if 'factory' in filename:
        return True
    
    # Check content
    if 'create' in content and ('return new' in content or 'return ' in content):
        return True
    
    # Language-specific checks
    if ext == '.py':
        if re.search(r'def create_\w+\(', content):
            return True
    elif ext in ['.js', '.ts']:
        if re.search(r'function create\w+\(', content) or re.search(r'create\w+\s*=\s*function', content):
            return True
    elif ext in ['.java', '.cs']:
        if 'abstract' in content and 'new' in content and ('protected' in content or 'public' in content):
            return True
    
    return False

async def detect_observer(file_path: str, content: str) -> bool:
    """Detect observer pattern"""
    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path).lower()
    
    # Check filename
    if 'observer' in filename or 'listener' in filename or 'event' in filename:
        return True
    
    # Check content for observer-related methods
    observer_methods = ['subscribe', 'unsubscribe', 'notify', 'addListener', 'removeListener', 'addEventListener', 'on(']
    if any(method in content for method in observer_methods):
        return True
    
    # Language-specific checks
    if ext == '.py':
        if re.search(r'def (notify|update|on_\w+)\(', content):
            return True
    elif ext in ['.js', '.ts']:
        # Check for event emitter pattern
        if 'emit(' in content and ('on(' in content or 'addEventListener' in content):
            return True
    elif ext in ['.java']:
        # Check for standard Java observer interfaces
        if 'implements Observer' in content or 'extends Observable' in content:
            return True
    
    return False

async def llm_pattern_detection(files_content: Dict[str, str], llm_service: LLMService) -> List[DesignPattern]:
    """Use LLM to detect more complex design patterns"""
    # Select a subset of files to analyze (to avoid overwhelming the LLM)
    selected_files = {}
    file_count = 0
    max_files = 10  # Adjust based on token limits
    
    # Prioritize files that are most likely to contain design patterns
    priority_files = [
        path for path in files_content.keys() 
        if any(keyword in os.path.basename(path).lower() for keyword in 
              ['factory', 'builder', 'adapter', 'decorator', 'strategy', 'proxy', 'service'])
    ]
    
    # Add priority files first
    for path in priority_files:
        if file_count < max_files:
            selected_files[path] = files_content[path]
            file_count += 1
    
    # Add other files until we reach the limit
    for path, content in files_content.items():
        if path not in selected_files and file_count < max_files:
            selected_files[path] = content
            file_count += 1
            
    # If we have no files, return empty list
    if not selected_files:
        return []
    
    # Use LLM to identify patterns
    llm_results = await llm_service.identify_design_patterns(selected_files)
    
    # Convert results to DesignPattern objects
    patterns = []
    for result in llm_results:
        if isinstance(result, dict) and 'name' in result and 'files' in result:
            # Ensure files exist in our codebase
            valid_files = [f for f in result.get('files', []) if f in files_content]
            if valid_files:
                patterns.append(DesignPattern(
                    name=result.get('name', 'Unknown Pattern'),
                    files=valid_files,
                    confidence=float(result.get('confidence', 0.5)),
                    description=result.get('description', 'No description provided')
                ))
    
    return patterns

async def deduplicate_patterns(patterns: List[DesignPattern]) -> List[DesignPattern]:
    """Deduplicate patterns based on name and files"""
    if not patterns:
        return []
    
    # Group by pattern name
    pattern_groups = {}
    for pattern in patterns:
        if pattern.name not in pattern_groups:
            pattern_groups[pattern.name] = []
        pattern_groups[pattern.name].append(pattern)
    
    # Merge patterns with the same name
    result = []
    for name, group in pattern_groups.items():
        if len(group) == 1:
            result.append(group[0])
        else:
            # Merge files and take the highest confidence
            all_files = set()
            max_confidence = 0.0
            descriptions = []
            
            for pattern in group:
                all_files.update(pattern.files)
                max_confidence = max(max_confidence, pattern.confidence)
                if pattern.description and pattern.description not in descriptions:
                    descriptions.append(pattern.description)
            
            # Create a merged pattern
            result.append(DesignPattern(
                name=name,
                files=list(all_files),
                confidence=max_confidence,
                description=max(descriptions, key=len) if descriptions else "No description provided"
            ))
    
    return result
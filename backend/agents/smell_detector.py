from typing import Dict, List, Any
import re
import os

class SmellDetector:
    """Detect code smells in source code files"""
    
    def __init__(self):
        self.smell_detectors = {
            "long_method": self._detect_long_method,
            "large_class": self._detect_large_class,
            "long_parameter_list": self._detect_long_parameter_list,
            "duplicate_code": self._detect_duplicate_code,
            "complex_conditional": self._detect_complex_conditional,
            "dead_code": self._detect_dead_code,
            "comment_overuse": self._detect_comment_overuse
        }
    
    async def detect_smells(self, file_path: str, content: str) -> List[Dict]:
        """Detect code smells in a file"""
        smells = []
        
        for smell_type, detector in self.smell_detectors.items():
            detected = await detector(file_path, content)
            smells.extend(detected)
        
        return smells
    
    async def _detect_long_method(self, file_path: str, content: str) -> List[Dict]:
        """Detect methods that are too long"""
        smells = []
        ext = os.path.splitext(file_path)[1].lower()
        lines = content.split('\n')
        
        # Define patterns for method/function declarations by language
        if ext == '.py':
            method_pattern = r'^\s*(async\s+)?def\s+(\w+)\s*\('
        elif ext in ['.js', '.ts']:
            method_pattern = r'^\s*(async\s+)?function\s+(\w+)\s*\(|^\s*(\w+)\s*[=:]\s*(async\s+)?\(?.*\)?\s*=>'
        elif ext in ['.java', '.cs']:
            method_pattern = r'^\s*(public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\('
        else:
            return []  # Unsupported language
        
        # Track current method and its lines
        current_method = None
        method_start_line = 0
        method_lines = 0
        
        for i, line in enumerate(lines):
            # Check if line marks the start of a method
            match = re.match(method_pattern, line)
            if match and not current_method:
                current_method = match.group(2) if match.group(2) else match.group(3)
                method_start_line = i
                method_lines = 0
            
            # Count lines in the current method
            if current_method:
                method_lines += 1
                
                # Check for method end (Python indentation or braces)
                if ext == '.py':
                    # Check if we've reached a new def with same or less indentation
                    if i > method_start_line and re.match(r'^\s*(async\s+)?def\s+', line):
                        leading_spaces_current = len(lines[method_start_line]) - len(lines[method_start_line].lstrip())
                        leading_spaces_new = len(line) - len(line.lstrip())
                        if leading_spaces_new <= leading_spaces_current:
                            # Method ended
                            if method_lines > 30:  # Threshold for long method
                                smells.append({
                                    "type": "long_method",
                                    "description": f"Method '{current_method}' is too long ({method_lines} lines)",
                                    "lines": f"{method_start_line+1}-{i}",
                                    "severity": "high" if method_lines > 50 else "medium"
                                })
                            current_method = None
                elif '}' in line and line.strip() == '}':
                    # Simple brace counting method end detection
                    if method_lines > 30:  # Threshold for long method
                        smells.append({
                            "type": "long_method",
                            "description": f"Method '{current_method}' is too long ({method_lines} lines)",
                            "lines": f"{method_start_line+1}-{i+1}",
                            "severity": "high" if method_lines > 50 else "medium"
                        })
                    current_method = None
        
        return smells
    
    async def _detect_large_class(self, file_path: str, content: str) -> List[Dict]:
        """Detect classes that are too large"""
        smells = []
        ext = os.path.splitext(file_path)[1].lower()
        lines = content.split('\n')
        
        # Define patterns for class declarations by language
        if ext == '.py':
            class_pattern = r'^\s*class\s+(\w+)'
        elif ext in ['.js', '.ts']:
            class_pattern = r'^\s*class\s+(\w+)'
        elif ext in ['.java', '.cs']:
            class_pattern = r'^\s*(public|private|protected|\s)+class\s+(\w+)'
        else:
            return []  # Unsupported language
        
        # Track current class and its metrics
        current_class = None
        class_start_line = 0
        class_lines = 0
        method_count = 0
        
        # Method detection patterns
        if ext == '.py':
            method_pattern = r'^\s*(async\s+)?def\s+(\w+)\s*\('
        elif ext in ['.js', '.ts']:
            method_pattern = r'^\s*(async\s+)?function\s+(\w+)\s*\(|^\s*(\w+)\s*[=:]\s*(async\s+)?\(?.*\)?\s*=>'
        elif ext in ['.java', '.cs']:
            method_pattern = r'^\s*(public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\('
        else:
            method_pattern = None
        
        for i, line in enumerate(lines):
            # Check if line marks the start of a class
            class_match = re.match(class_pattern, line)
            if class_match and not current_class:
                group_idx = 2 if ext in ['.java', '.cs'] else 1
                current_class = class_match.group(group_idx)
                class_start_line = i
                class_lines = 0
                method_count = 0
            
            # Count lines and methods in the current class
            if current_class:
                class_lines += 1
                
                # Count methods
                if method_pattern and re.match(method_pattern, line):
                    method_count += 1
                
                # Check for class end (Python indentation or braces)
                if ext == '.py':
                    if i > class_start_line and re.match(r'^\s*class\s+', line):
                        leading_spaces_current = len(lines[class_start_line]) - len(lines[class_start_line].lstrip())
                        leading_spaces_new = len(line) - len(line.lstrip())
                        if leading_spaces_new <= leading_spaces_current:
                            # Class ended
                            if class_lines > 200 or method_count > 10:
                                smells.append({
                                    "type": "large_class",
                                    "description": f"Class '{current_class}' is too large ({class_lines} lines, {method_count} methods)",
                                    "lines": f"{class_start_line+1}-{i}",
                                    "severity": "high" if class_lines > 300 or method_count > 15 else "medium"
                                })
                            current_class = None
                elif '}' in line and line.strip() == '}' and i > class_start_line + 5:
                    # Simple brace counting class end detection (with minimum size check)
                    if class_lines > 200 or method_count > 10:
                        smells.append({
                            "type": "large_class",
                            "description": f"Class '{current_class}' is too large ({class_lines} lines, {method_count} methods)",
                            "lines": f"{class_start_line+1}-{i+1}",
                            "severity": "high" if class_lines > 300 or method_count > 15 else "medium"
                        })
                    current_class = None
        
        return smells
    
    async def _detect_long_parameter_list(self, file_path: str, content: str) -> List[Dict]:
        """Detect methods with too many parameters"""
        smells = []
        ext = os.path.splitext(file_path)[1].lower()
        lines = content.split('\n')
        
        # Define patterns for method declarations with parameter lists
        if ext == '.py':
            method_pattern = r'^\s*(async\s+)?def\s+(\w+)\s*\(([^)]*)\)'
        elif ext in ['.js', '.ts']:
            method_pattern = r'^\s*(async\s+)?function\s+(\w+)\s*\(([^)]*)\)|^\s*(\w+)\s*[=:]\s*(async\s+)?\(([^)]*)\)'
        elif ext in ['.java', '.cs']:
            method_pattern = r'^\s*(public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\(([^)]*)\)'
        else:
            return []  # Unsupported language
        
        for i, line in enumerate(lines):
            # Look for method declarations
            match = re.match(method_pattern, line)
            if match:
                # Extract parameter list
                params = match.group(3) if ext in ['.py', '.java', '.cs'] else (match.group(3) or match.group(6))
                
                # Skip empty parameters
                if not params or params.strip() == '':
                    continue
                    
                # Count parameters
                param_count = len([p for p in params.split(',') if p.strip()])
                
                # Check if parameter count exceeds threshold
                if param_count > 4:
                    method_name = match.group(2) if ext in ['.py', '.java', '.cs'] else (match.group(2) or match.group(4))
                    smells.append({
                        "type": "long_parameter_list",
                        "description": f"Method '{method_name}' has too many parameters ({param_count})",
                        "lines": f"{i+1}",
                        "severity": "high" if param_count > 6 else "medium"
                    })
        
        return smells
    
    async def _detect_duplicate_code(self, file_path: str, content: str) -> List[Dict]:
        """Basic detection of duplicate code blocks (simplified for MVP)"""
        smells = []
        lines = content.split('\n')
        
        # Simple approach: look for blocks of 6+ identical lines
        block_size = 6
        seen_blocks = {}
        
        for i in range(len(lines) - block_size + 1):
            block = '\n'.join(lines[i:i+block_size])
            # Skip empty or comment-only blocks
            if all(line.strip() == '' or line.strip().startswith(('#', '//', '/*')) for line in lines[i:i+block_size]):
                continue
                
            if block in seen_blocks:
                first_occurrence = seen_blocks[block]
                smells.append({
                    "type": "duplicate_code",
                    "description": f"Duplicate code block found",
                    "lines": f"{i+1}-{i+block_size}, {first_occurrence+1}-{first_occurrence+block_size}",
                    "severity": "medium"
                })
            else:
                seen_blocks[block] = i
        
        return smells
    
    async def _detect_complex_conditional(self, file_path: str, content: str) -> List[Dict]:
        """Detect overly complex conditional expressions"""
        smells = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Look for if statements with multiple conditions
            if 'if ' in line or 'elif ' in line:
                and_count = line.count(' and ')
                or_count = line.count(' or ')
                not_count = line.count(' not ')
                operator_count = and_count + or_count + not_count
                
                # Check for nested ternary expressions
                ternary_count = line.count('?') + line.count(':')
                
                # Check complexity threshold
                if operator_count > 2 or ternary_count > 2:
                    smells.append({
                        "type": "complex_conditional",
                        "description": f"Complex conditional with {operator_count} logical operators",
                        "lines": f"{i+1}",
                        "severity": "high" if operator_count > 4 else "medium"
                    })
        
        return smells
    
    async def _detect_dead_code(self, file_path: str, content: str) -> List[Dict]:
        """Detect commented-out code and potential unused code"""
        smells = []
        lines = content.split('\n')
        ext = os.path.splitext(file_path)[1].lower()
        
        # Check for commented-out code blocks
        comment_block_start = None
        consecutive_comments = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check if line is a comment
            is_comment = False
            if ext == '.py':
                is_comment = stripped.startswith('#')
            elif ext in ['.js', '.ts', '.java', '.cs', '.c', '.cpp']:
                is_comment = stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*')
            
            if is_comment:
                consecutive_comments += 1
                if comment_block_start is None:
                    comment_block_start = i
                
                # Look for code-like patterns in comments
                code_indicators = ['if', 'for', 'while', 'function', 'class', 'return', 'var ', 'let ', 'const ']
                has_code = any(indicator in stripped for indicator in code_indicators)
                
                if has_code and consecutive_comments >= 3:
                    smells.append({
                        "type": "dead_code",
                        "description": "Block of commented-out code",
                        "lines": f"{comment_block_start+1}-{i+1}",
                        "severity": "medium"
                    })
                    comment_block_start = None
                    consecutive_comments = 0
            else:
                comment_block_start = None
                consecutive_comments = 0
        
        return smells
    
    async def _detect_comment_overuse(self, file_path: str, content: str) -> List[Dict]:
        """Detect excessive comments that could indicate code smell"""
        smells = []
        lines = content.split('\n')
        ext = os.path.splitext(file_path)[1].lower()
        
        comment_lines = 0
        code_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
                
            # Check if line is a comment
            is_comment = False
            if ext == '.py':
                is_comment = stripped.startswith('#')
            elif ext in ['.js', '.ts', '.java', '.cs', '.c', '.cpp']:
                is_comment = stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*')
            
            if is_comment:
                comment_lines += 1
            else:
                code_lines += 1
        
        # Calculate comment to code ratio
        if code_lines > 0:
            comment_ratio = comment_lines / code_lines
            if comment_ratio > 0.4:  # Threshold for excessive comments
                smells.append({
                    "type": "comment_overuse",
                    "description": f"Excessive comments ({int(comment_ratio*100)}% comment-to-code ratio)",
                    "lines": "entire file",
                    "severity": "low" if comment_ratio < 0.6 else "medium"
                })
        
        return smells

# Create an instance to be imported by other modules
smell_detector = SmellDetector()
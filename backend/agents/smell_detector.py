import logging
from typing import Dict, List, Any
import re
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

class SmellDetector:
    """Agent responsible for detecting code smells in files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define quick smell detectors for pre-screening
        self.smell_detectors = {
            "long_method": {
                "description": "Method that has grown too large",
                "detector": self._detect_long_method,
                "severity": "medium",
            },
            "large_class": {
                "description": "Class that has taken on too many responsibilities",
                "detector": self._detect_large_class,
                "severity": "medium",
            },
            "long_parameter_list": {
                "description": "Method with excessive parameters",
                "detector": self._detect_long_parameter_list,
                "severity": "medium",
            },
            "duplicate_code": {
                "description": "Similar code structure repeated",
                "detector": self._detect_duplicate_code,
                "severity": "high",
            },
            "complex_conditional": {
                "description": "Overly complex conditional expression",
                "detector": self._detect_complex_conditional,
                "severity": "medium",
            },
            "dead_code": {
                "description": "Code that is never executed",
                "detector": self._detect_dead_code,
                "severity": "low",
            },
            "comment_overuse": {
                "description": "Excessive comments that may mask bad code",
                "detector": self._detect_comment_overuse,
                "severity": "low",
            },
        }
    
    async def analyze_file_smells(self, file_path: str, file_content: str, repository_context: Dict) -> Dict:
        """Analyze a file for code smells"""
        try:
            # Extract file extension
            file_ext = file_path.split(".")[-1].lower() if "." in file_path else ""
            
            # Pre-screen for potential smells
            potential_smells = self._pre_screen_smells(file_content, file_ext)
            
            # Add smell context to repository context
            enhanced_context = repository_context.copy()
            enhanced_context["potential_smells"] = potential_smells
            
            # Get detailed analysis from LLM
            return await llm_service.analyze_file(file_path, file_content, enhanced_context)
            
        except Exception as e:
            self.logger.exception(f"Error in smell detection for {file_path}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error in smell detection: {str(e)}",
                "file_path": file_path
            }
    
    def _pre_screen_smells(self, file_content: str, file_ext: str) -> List[Dict]:
        """Pre-screen file content for potential code smells"""
        potential_smells = []
        
        # Apply each detector
        for smell_id, smell_info in self.smell_detectors.items():
            detector = smell_info["detector"]
            results = detector(file_content, file_ext)
            
            if results:
                for result in results:
                    smell = {
                        "type": smell_id,
                        "description": smell_info["description"],
                        "severity": smell_info["severity"],
                        "lines": result.get("lines", "unknown"),
                        "details": result.get("details", "")
                    }
                    potential_smells.append(smell)
        
        return potential_smells
    
    def _detect_long_method(self, content: str, file_ext: str) -> List[Dict]:
        """Detect long methods in the code"""
        results = []
        
        # Adapt method detection based on language
        if file_ext in ["py"]:
            # Detect Python functions/methods
            pattern = r"def\s+(\w+)\s*\(.*?\):"
            methods = re.finditer(pattern, content, re.DOTALL)
            
            for method in methods:
                method_name = method.group(1)
                method_start = method.start()
                
                # Find method body
                lines_after = content[method_start:].split("\n")
                line_count = 0
                indentation = None
                method_end = method_start
                
                for i, line in enumerate(lines_after):
                    if i == 0:  # First line with the def
                        line_count += 1
                        continue
                        
                    if line.strip() == "" or line.strip().startswith("#"):
                        continue
                        
                    if indentation is None:
                        # First non-empty line after def determines indentation
                        spaces = len(line) - len(line.lstrip())
                        if spaces > 0:
                            indentation = spaces
                            line_count += 1
                        else:
                            # No indentation means method is over
                            break
                    else:
                        # Check if we're still in the method
                        spaces = len(line) - len(line.lstrip())
                        if spaces >= indentation:
                            line_count += 1
                            method_end += len(line) + 1  # +1 for newline
                        else:
                            break
                
                if line_count > 20:  # Long method threshold
                    results.append({
                        "lines": f"Method {method_name}: {line_count} lines",
                        "details": f"Method '{method_name}' is too long ({line_count} lines). Consider breaking it down."
                    })
        
        elif file_ext in ["js", "ts", "jsx", "tsx"]:
            # Detect JavaScript/TypeScript functions/methods
            # Function declarations
            patterns = [
                r"function\s+(\w+)\s*\(.*?\)\s*{", 
                r"(?:const|let|var)\s+(\w+)\s*=\s*function\s*\(.*?\)\s*{",
                r"(?:const|let|var)\s+(\w+)\s*=\s*\(.*?\)\s*=>",
                r"(\w+)\s*\(.*?\)\s*{" # Object methods
            ]
            
            for pattern in patterns:
                functions = re.finditer(pattern, content, re.DOTALL)
                for func in functions:
                    func_name = func.group(1)
                    func_start = func.start()
                    
                    # Count brace level to find end of function
                    brace_level = 0
                    in_string = False
                    string_char = None
                    func_end = func_start
                    
                    for i, char in enumerate(content[func_start:]):
                        if char == '"' or char == "'" or char == '`':
                            if not in_string:
                                in_string = True
                                string_char = char
                            elif string_char == char:
                                in_string = False
                        elif not in_string:
                            if char == '{':
                                brace_level += 1
                            elif char == '}':
                                brace_level -= 1
                                if brace_level == 0:
                                    func_end = func_start + i
                                    break
                    
                    func_content = content[func_start:func_end+1]
                    line_count = func_content.count('\n')
                    
                    if line_count > 15:  # Long method threshold for JS
                        results.append({
                            "lines": f"Function {func_name}: {line_count} lines",
                            "details": f"Function '{func_name}' is too long ({line_count} lines). Consider breaking it down."
                        })
        
        elif file_ext in ["java", "c", "cpp", "cs"]:
            # Detect methods in C-like languages
            pattern = r"(?:public|private|protected|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\) *\{?"
            methods = re.finditer(pattern, content, re.DOTALL)
            
            for method in methods:
                method_name = method.group(1)
                method_start = method.start()
                
                # Count brace level to find end of method
                brace_level = 0
                in_string = False
                func_end = method_start
                
                for i, char in enumerate(content[method_start:]):
                    if char == '"':
                        in_string = not in_string
                    elif not in_string:
                        if char == '{':
                            brace_level += 1
                        elif char == '}':
                            brace_level -= 1
                            if brace_level == 0:
                                func_end = method_start + i
                                break
                
                method_content = content[method_start:func_end+1]
                line_count = method_content.count('\n')
                
                if line_count > 20:  # Long method threshold
                    results.append({
                        "lines": f"Method {method_name}: {line_count} lines",
                        "details": f"Method '{method_name}' is too long ({line_count} lines). Consider breaking it down."
                    })
        
        return results
    
    def _detect_large_class(self, content: str, file_ext: str) -> List[Dict]:
        """Detect large classes in the code"""
        results = []
        
        # Adapt class detection based on language
        if file_ext in ["py"]:
            # Detect Python classes
            pattern = r"class\s+(\w+)\s*(?:\(.*?\))?:"
            classes = re.finditer(pattern, content, re.DOTALL)
            
            for cls in classes:
                class_name = cls.group(1)
                
                # Count method definitions within the class
                method_pattern = r"def\s+(\w+)\s*\("
                methods = re.findall(method_pattern, content[cls.start():], re.DOTALL)
                
                if len(methods) > 10:  # Large class threshold
                    results.append({
                        "lines": f"Class {class_name}: {len(methods)} methods",
                        "details": f"Class '{class_name}' has too many methods ({len(methods)}). Consider breaking it down."
                    })
        
        elif file_ext in ["java", "c", "cpp", "cs"]:
            # Detect classes in C-like languages
            pattern = r"class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+\w+(?:\s*,\s*\w+)*)?\s*\{"
            classes = re.finditer(pattern, content, re.DOTALL)
            
            for cls in classes:
                class_name = cls.group(1)
                class_start = cls.start()
                
                # Count method definitions within the class
                method_pattern = r"(?:public|private|protected|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\) *\{?"
                methods = re.findall(method_pattern, content[class_start:], re.DOTALL)
                
                if len(methods) > 10:  # Large class threshold
                    results.append({
                        "lines": f"Class {class_name}: {len(methods)} methods",
                        "details": f"Class '{class_name}' has too many methods ({len(methods)}). Consider breaking it down."
                    })
        
        elif file_ext in ["js", "ts"]:
            # Detect JavaScript/TypeScript classes
            pattern = r"class\s+(\w+)(?:\s+extends\s+\w+)?\s*\{"
            classes = re.finditer(pattern, content, re.DOTALL)
            
            for cls in classes:
                class_name = cls.group(1)
                class_start = cls.start()
                
                # Count method definitions within the class
                method_pattern = r"(?:async\s+)?(\w+)\s*\(.*?\)\s*\{|\(.*?\)\s*=>|get\s+(\w+)\s*\(|set\s+(\w+)\s*\("
                methods = re.findall(method_pattern, content[class_start:], re.DOTALL)
                
                if len(methods) > 8:  # Large class threshold for JS
                    results.append({
                        "lines": f"Class {class_name}: {len(methods)} methods",
                        "details": f"Class '{class_name}' has too many methods ({len(methods)}). Consider breaking it down."
                    })
        
        return results
    
    def _detect_long_parameter_list(self, content: str, file_ext: str) -> List[Dict]:
        """Detect methods with too many parameters"""
        results = []
        
        # Generic pattern for function definitions with parameters
        patterns = [
            # Python functions
            r"def\s+(\w+)\s*\((.*?)\):",
            # JavaScript/TypeScript functions
            r"function\s+(\w+)\s*\((.*?)\)",
            r"(?:const|let|var)\s+(\w+)\s*=\s*function\s*\((.*?)\)",
            r"(?:const|let|var)\s+(\w+)\s*=\s*\((.*?)\)\s*=>",
            # Java/C#/C++ methods
            r"(?:public|private|protected|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\((.*?)\)",
            # Object methods
            r"(\w+)\s*\((.*?)\)\s*\{"
        ]
        
        for pattern in patterns:
            functions = re.finditer(pattern, content, re.DOTALL)
            
            for func in functions:
                func_name = func.group(1)
                params = func.group(2).strip()
                
                if not params:
                    continue
                
                # Count commas to determine parameter count
                # This is a simple approach and might not be accurate for all cases
                param_count = 1 + params.count(',')
                
                # Check if we have default parameters or destructuring
                if "=" in params:
                    param_count = len([p for p in params.split(',') if p.strip()])
                
                # Define thresholds based on language
                threshold = 4  # Default threshold
                if file_ext in ["py"]:
                    threshold = 5  # Python threshold
                elif file_ext in ["js", "ts"]:
                    threshold = 3  # JavaScript/TypeScript threshold
                
                if param_count > threshold:
                    results.append({
                        "lines": f"Function {func_name}: {param_count} parameters",
                        "details": f"Function '{func_name}' has too many parameters ({param_count}). Consider using parameter objects or restructuring."
                    })
        
        return results
    
    def _detect_duplicate_code(self, content: str, file_ext: str) -> List[Dict]:
        """Detect duplicate code blocks"""
        results = []
        
        # This is a simplified approach - only detecting identical non-trivial lines
        lines = content.split('\n')
        line_dict = {}
        
        # Minimum meaningful line length to consider
        min_line_length = 30
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Skip empty lines, comments, and short lines
            if (not stripped_line or 
                stripped_line.startswith('#') or 
                stripped_line.startswith('//') or 
                stripped_line.startswith('/*') or 
                stripped_line.startswith('*') or 
                len(stripped_line) < min_line_length):
                continue
            
            if stripped_line in line_dict:
                line_dict[stripped_line].append(i + 1)  # +1 for 1-based line numbering
            else:
                line_dict[stripped_line] = [i + 1]
        
        # Report lines that appear multiple times
        for line, occurrences in line_dict.items():
            if len(occurrences) > 1:
                results.append({
                    "lines": f"Lines {', '.join(map(str, occurrences))}",
                    "details": f"Duplicate code detected: '{line[:50]}...' appears {len(occurrences)} times."
                })
        
        return results
    
    def _detect_complex_conditional(self, content: str, file_ext: str) -> List[Dict]:
        """Detect overly complex conditional expressions"""
        results = []
        
        # Look for if statements with multiple conditions
        patterns = [
            r"if\s+(.+?):",  # Python
            r"if\s*\((.+?)\)",  # C-like and JavaScript
        ]
        
        for pattern in patterns:
            conditionals = re.finditer(pattern, content, re.DOTALL)
            
            for cond in conditionals:
                condition = cond.group(1).strip()
                
                # Count logical operators
                and_count = condition.count(' and ') + condition.count(' && ')
                or_count = condition.count(' or ') + condition.count(' || ')
                operator_count = and_count + or_count
                
                # Count nested parentheses as an indicator of complexity
                open_paren = condition.count('(')
                close_paren = condition.count(')')
                if open_paren != close_paren:
                    # Skip if the parentheses don't match - might be a parsing issue
                    continue
                
                # Calculate line number
                line_num = content[:cond.start()].count('\n') + 1
                
                # Define complexity threshold
                if (operator_count > 3) or (open_paren > 2):
                    complexity = "high" if operator_count > 5 or open_paren > 4 else "medium"
                    results.append({
                        "lines": f"Line {line_num}",
                        "details": f"Complex conditional with {operator_count} logical operators and {open_paren} parentheses groupings. Consider extracting conditions to helper methods."
                    })
        
        return results
    
    def _detect_dead_code(self, content: str, file_ext: str) -> List[Dict]:
        """Detect potentially dead code (simple heuristics)"""
        results = []
        
        # Look for commented out code blocks
        patterns = [
            r"# *(?:def|class|if|for|while).*?(?:\n# .*?)*",  # Python commented code
            r"\/\/.*(?:function|class|if|for|while).*(?:\n\/\/.*)*",  # JS/C commented code
            r"\/\*.*?(?:function|class|if|for|while).*?\*\/",  # Multi-line comments
        ]
        
        for pattern in patterns:
            comments = re.finditer(pattern, content, re.DOTALL)
            
            for comment in comments:
                comment_text = comment.group(0)
                if len(comment_text.split('\n')) > 2:  # Only report multi-line commented code
                    line_num = content[:comment.start()].count('\n') + 1
                    results.append({
                        "lines": f"Starting at line {line_num}",
                        "details": f"Potential dead code detected: Multi-line commented out code block."
                    })
        
        # Look for unreachable code after return/break/continue
        if file_ext in ["py", "js", "ts"]:
            lines = content.split('\n')
            
            for i in range(len(lines) - 1):
                line = lines[i].strip()
                next_line = lines[i + 1].strip()
                
                # If we have a return/break/continue and the next line is not empty or a comment and has the same indentation
                if (line.startswith("return ") or line == "return" or 
                    line == "break" or line == "continue"):
                    
                    # Get indentation levels
                    current_indent = len(lines[i]) - len(lines[i].lstrip())
                    next_indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                    
                    # Check if the next line has the same or less indentation (could be unreachable)
                    if (next_indent <= current_indent and 
                        next_line and 
                        not next_line.startswith("#") and 
                        not next_line.startswith("//") and
                        not next_line.startswith("else") and
                        not next_line.startswith("elif") and
                        not next_line.startswith("except") and
                        not next_line.startswith("finally")):
                        
                        results.append({
                            "lines": f"Lines {i+1}-{i+2}",
                            "details": f"Potential unreachable code detected after {line}."
                        })
        
        return results
    
    def _detect_comment_overuse(self, content: str, file_ext: str) -> List[Dict]:
        """Detect excessive comments that might mask bad code"""
        results = []
        
        # Count lines and comment lines
        lines = content.split('\n')
        total_lines = len(lines)
        
        comment_lines = 0
        code_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # Count comment lines based on language
            if file_ext in ["py"]:
                if stripped.startswith('#'):
                    comment_lines += 1
                else:
                    code_lines += 1
            elif file_ext in ["js", "ts", "java", "c", "cpp", "cs"]:
                if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                    comment_lines += 1
                else:
                    code_lines += 1
        
        # Skip if the file is too small
        if total_lines < 10:
            return results
        
        # Calculate comment to code ratio
        if code_lines > 0:
            comment_ratio = comment_lines / code_lines
            
            if comment_ratio > 0.5:  # More than 50% comments
                results.append({
                    "lines": f"Throughout file: {comment_lines} comment lines, {code_lines} code lines",
                    "details": f"High comment to code ratio ({comment_ratio:.2f}). Excessive comments might be masking unclear code. Consider refactoring the code to be more self-documenting."
                })
        
        return results
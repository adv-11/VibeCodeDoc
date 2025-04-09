import logging
import os
import json
from typing import Dict, List, Any, Optional
import openai
from config.settings import settings

logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = settings.LLM_API_KEY

class LLMService:
    """Service to interact with LLMs for code analysis tasks"""
    
    def __init__(self):
        self.model = settings.LLM_MODEL
        
        # Load reference materials about code smells and refactoring techniques
        self.code_smells_reference = self._load_reference_material("code_smells")
        self.refactoring_techniques_reference = self._load_reference_material("refactoring_techniques")
        self.design_patterns_reference = self._load_reference_material("design_patterns")
    
    def _load_reference_material(self, reference_type: str) -> str:
        """Load reference material for context enhancement"""
        # In a real implementation, you would load these from files
        if reference_type == "code_smells":
            return """
            # Code Smells Reference
            Code smells are indicators of potential problems in code that may require refactoring.
            
            ## Bloaters
            - Long Method: A method that has grown too large
            - Large Class: A class that has taken on too many responsibilities
            - Primitive Obsession: Using primitives instead of small objects for simple tasks
            - Long Parameter List: More than three or four parameters for a method
            - Data Clumps: Different parts of the code containing identical groups of variables
            
            ## Object-Orientation Abusers
            - Switch Statements: Complex switch or if statements
            - Temporary Field: An instance variable that is only set in certain circumstances
            - Refused Bequest: A subclass uses only some of the methods and properties inherited from its parents
            - Alternative Classes with Different Interfaces: Two classes perform similar functions but have different method names
            
            ## Change Preventers
            - Divergent Change: One class is commonly changed in different ways for different reasons
            - Shotgun Surgery: A change requires making many small changes to many different classes
            - Parallel Inheritance Hierarchies: Creating a subclass for one class requires creating a subclass for another
            
            ## Dispensables
            - Comments: Excess comments may be masking bad code
            - Duplicate Code: Two code fragments look almost identical
            - Lazy Class: A class that does too little
            - Data Class: A class with fields and getters/setters only
            - Dead Code: A variable, parameter, field, method or class is no longer used
            - Speculative Generality: Unused "just in case" code
            
            ## Couplers
            - Feature Envy: A method that seems more interested in a class other than the one it belongs to
            - Inappropriate Intimacy: One class uses the internal fields and methods of another class
            - Message Chains: A chain of method calls to navigate to the desired object
            - Middle Man: A class that delegates most of its work to other classes
            """
        elif reference_type == "refactoring_techniques":
            return """
            # Refactoring Techniques Reference
            
            ## Composing Methods
            - Extract Method: Turn code fragment into method
            - Inline Method: Replace method call with method body
            - Extract Variable: Put expression result in a variable
            - Inline Temp: Replace temp with the expression
            - Replace Temp with Query: Replace temp with a query method
            - Split Temporary Variable: Split a temp variable used twice for different purposes
            - Remove Assignments to Parameters: Use a local variable instead of a parameter
            - Replace Method with Method Object: Turn method into separate object
            - Substitute Algorithm: Replace algorithm with clearer one
            
            ## Moving Features Between Objects
            - Move Method: Move method to another class
            - Move Field: Move field to another class
            - Extract Class: Create new class and move fields/methods
            - Inline Class: Move all features of a class into another class
            - Hide Delegate: Hide delegation through encapsulation
            - Remove Middle Man: Let clients call delegate directly
            - Introduce Foreign Method: Add method to client with reference to the service
            - Introduce Local Extension: Create a subclass to add functionality
            
            ## Organizing Data
            - Self Encapsulate Field: Use getters/setters
            - Replace Data Value with Object: Replace data item with an object
            - Change Value to Reference: Replace duplicate objects with a single reference object
            - Change Reference to Value: Replace reference object with a value object
            - Replace Array with Object: Replace array with object with named properties
            - Duplicate Observed Data: Split GUI and domain data
            - Change Unidirectional Association to Bidirectional: Add pointer to back reference
            - Change Bidirectional Association to Unidirectional: Remove pointer that isn't needed
            - Replace Magic Number with Symbolic Constant: Replace number with named constant
            - Encapsulate Field: Make public field private
            - Encapsulate Collection: Return copy of collection
            - Replace Record with Data Class: Replace record with data object
            - Replace Type Code with Class: Replace type code with a class
            - Replace Type Code with Subclasses: Replace type code with subclasses
            - Replace Type Code with State/Strategy: Replace type code with state objects
            - Replace Subclass with Fields: Replace subclasses with fields in the superclass
            
            ## Simplifying Conditional Expressions
            - Decompose Conditional: Split complex conditional into methods
            - Consolidate Conditional Expression: Combine related conditionals
            - Consolidate Duplicate Conditional: Combine duplicate code in conditionals
            - Remove Control Flag: Replace control flag with break or return
            - Replace Nested Conditional with Guard Clauses: Replace nested conditionals with guard clauses
            - Replace Conditional with Polymorphism: Replace conditional with polymorphic method
            - Introduce Null Object: Replace null checks with a null object
            - Introduce Assertion: Add assertions to clarify assumptions
            
            ## Simplifying Method Calls
            - Rename Method: Change method name to better reflect purpose
            - Add Parameter: Add parameter to method
            - Remove Parameter: Remove unused parameter
            - Separate Query from Modifier: Split method into query and modifier
            - Parameterize Method: Replace multiple similar methods with parameterized method
            - Replace Parameter with Explicit Methods: Replace parameter with multiple methods
            - Preserve Whole Object: Pass whole object instead of individual values
            - Replace Parameter with Method Call: Replace parameter with call to a method
            - Introduce Parameter Object: Replace parameter group with object
            - Remove Setting Method: Remove setter method for immutable field
            - Hide Method: Make method private or protected
            - Replace Constructor with Factory Method: Replace constructor with factory method
            - Encapsulate Downcast: Move downcasting to within the method
            - Replace Error Code with Exception: Replace error code with exception
            - Replace Exception with Test: Replace exception with test
            
            ## Dealing with Generalization
            - Pull Up Field: Move field from subclasses to superclass
            - Pull Up Method: Move method from subclasses to superclass
            - Pull Up Constructor Body: Move constructor body to superclass
            - Push Down Method: Move method to subclasses
            - Push Down Field: Move field to subclasses
            - Extract Subclass: Create subclass for variants
            - Extract Superclass: Create superclass for common features
            - Extract Interface: Extract interface for part of class
            - Collapse Hierarchy: Merge superclass and subclass
            - Form Template Method: Create template methods in subclasses
            - Replace Inheritance with Delegation: Replace inheritance with delegation
            - Replace Delegation with Inheritance: Replace delegation with inheritance
            """
        elif reference_type == "design_patterns":
            return """
            # Design Patterns Reference
            
            ## Creational Patterns
            - Factory Method: Define an interface for creating an object, but let subclasses decide which class to instantiate
            - Abstract Factory: Provide an interface for creating families of related or dependent objects
            - Builder: Separate the construction of a complex object from its representation
            - Prototype: Specify the kinds of objects to create using a prototypical instance
            - Singleton: Ensure a class has only one instance and provide a global point of access to it
            
            ## Structural Patterns
            - Adapter: Convert the interface of a class into another interface clients expect
            - Bridge: Decouple an abstraction from its implementation
            - Composite: Compose objects into tree structures to represent part-whole hierarchies
            - Decorator: Attach additional responsibilities to an object dynamically
            - Facade: Provide a unified interface to a set of interfaces in a subsystem
            - Flyweight: Use sharing to support large numbers of fine-grained objects efficiently
            - Proxy: Provide a surrogate or placeholder for another object to control access to it
            
            ## Behavioral Patterns
            - Chain of Responsibility: Avoid coupling the sender of a request to its receiver
            - Command: Encapsulate a request as an object
            - Iterator: Provide a way to access the elements of an aggregate object sequentially
            - Mediator: Define an object that encapsulates how a set of objects interact
            - Memento: Capture and externalize an object's internal state
            - Observer: Define a one-to-many dependency between objects
            - State: Allow an object to alter its behavior when its internal state changes
            - Strategy: Define a family of algorithms, encapsulate each one, and make them interchangeable
            - Template Method: Define the skeleton of an algorithm in an operation
            - Visitor: Represent an operation to be performed on elements of an object structure
            """
        return ""

    async def analyze_file(self, file_path: str, file_content: str, repository_context: Dict) -> Dict:
        """Analyze a single file using the LLM"""
        try:
            # Prepare the context for the LLM
            context = self._prepare_file_analysis_context(file_path, repository_context)
            
            # Prepare the prompt
            prompt = self._create_file_analysis_prompt(file_path, file_content, context)
            
            # Call the LLM
            response = await self._call_llm(prompt)
            
            # Process the response
            return self._process_file_analysis_response(response)
            
        except Exception as e:
            logger.exception(f"Error analyzing file {file_path}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error analyzing file: {str(e)}",
                "file_path": file_path
            }
    
    async def analyze_repository_structure(self, repository: Dict) -> Dict:
        """Analyze the overall structure of the repository"""
        try:
            # Extract relevant information
            structure = repository["structure"]
            file_count = len(repository["files"])
            
            # Prepare the prompt
            prompt = self._create_repository_structure_prompt(repository)
            
            # Call the LLM
            response = await self._call_llm(prompt)
            
            # Process the response
            return self._process_repository_analysis_response(response)
            
        except Exception as e:
            logger.exception(f"Error analyzing repository structure: {str(e)}")
            return {
                "status": "error",
                "message": f"Error analyzing repository structure: {str(e)}"
            }
    
    async def generate_final_report(self, repo_data: Dict, file_analyses: List[Dict], structure_analysis: Dict) -> Dict:
        """Generate a final comprehensive report based on all analyses"""
        try:
            # Prepare the prompt
            prompt = self._create_final_report_prompt(repo_data, file_analyses, structure_analysis)
            
            # Call the LLM
            response = await self._call_llm(prompt)
            
            # Process the response
            return self._process_final_report_response(response)
            
        except Exception as e:
            logger.exception(f"Error generating final report: {str(e)}")
            return {
                "status": "error",
                "message": f"Error generating final report: {str(e)}"
            }
    
    def _prepare_file_analysis_context(self, file_path: str, repository_context: Dict) -> Dict:
        """Prepare context information for file analysis"""
        extension = os.path.splitext(file_path)[1].lower()
        
        # Determine language based on file extension
        language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "React JSX",
            ".tsx": "React TSX",
            ".java": "Java",
            ".c": "C",
            ".cpp": "C++",
            ".cs": "C#",
            ".go": "Go",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".rs": "Rust",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".json": "JSON",
            ".md": "Markdown",
        }
        
        language = language_map.get(extension, "Unknown")
        
        return {
            "language": language,
            "extension": extension,
            "repository_name": repository_context.get("name", ""),
            "repository_owner": repository_context.get("owner", ""),
        }
    
    def _create_file_analysis_prompt(self, file_path: str, file_content: str, context: Dict) -> str:
        """Create a prompt for analyzing a single file"""
        return f"""
        You are an expert code analyst with deep knowledge of software design patterns, code smells, and refactoring techniques.
        
        # Task
        Analyze the following {context['language']} file and identify:
        1. Code smells present in the file
        2. Design patterns that are used or could be applied
        3. Refactoring techniques that would improve the code
        4. Assign a quality score from 1-10
        
        # File Information
        - Path: {file_path}
        - Language: {context['language']}
        - Repository: {context['repository_name']} by {context['repository_owner']}
        
        # Code Analysis Reference
        ## Code Smells
        {self.code_smells_reference}
        
        ## Refactoring Techniques
        {self.refactoring_techniques_reference}
        
        ## Design Patterns
        {self.design_patterns_reference}
        
        # File Content
        ```{context['language'].lower()}
        {file_content}
        ```
        
        # Response Format
        Provide your analysis in the following JSON format:
        ```json
        {{
            "file_path": "{file_path}",
            "language": "{context['language']}",
            "analysis": {{
                "summary": "Brief overall assessment",
                "code_smells": [
                    {{
                        "type": "smell type",
                        "description": "description of the issue",
                        "lines": "line numbers or range",
                        "severity": "low|medium|high"
                    }}
                ],
                "design_patterns": [
                    {{
                        "pattern": "pattern name",
                        "status": "used|could be applied",
                        "description": "how it's used or could be applied"
                    }}
                ],
                "refactoring_opportunities": [
                    {{
                        "technique": "refactoring technique",
                        "description": "how to apply it",
                        "target": "specific code area"
                    }}
                ],
                "quality_score": 5,
                "score_explanation": "Explanation of the score"
            }}
        }}
        ```
        
        Provide ONLY the JSON response with no additional text. Ensure the JSON is valid.
        """
    
    def _create_repository_structure_prompt(self, repository: Dict) -> str:
        """Create a prompt for analyzing the repository structure"""
        # Convert structure to a string representation
        structure_repr = json.dumps(repository["structure"], indent=2)
        
        file_count = len(repository["files"])
        file_extensions = {file["extension"] for file in repository["files"] if "extension" in file}
        
        return f"""
        You are an expert software architect with deep knowledge of project structures and organization patterns.
        
        # Task
        Analyze the structure of this repository and provide insights on:
        1. Overall architecture pattern (if discernible)
        2. Directory organization and structure quality
        3. Code organization issues or improvements
        4. Adherence to common project structure patterns for the detected languages
        
        # Repository Information
        - Name: {repository["repository"]["name"]}
        - Owner: {repository["repository"]["owner"]}
        - File count: {file_count}
        - File types: {", ".join(file_extensions)}
        
        # Repository Structure
        ```json
        {structure_repr}
        ```
        
        # Response Format
        Provide your analysis in the following JSON format:
        ```json
        {{
            "architecture_analysis": {{
                "detected_pattern": "Detected architecture pattern or 'Unclear'",
                "structure_quality_score": 5,
                "directory_organization": "Assessment of directory organization",
                "structure_issues": [
                    {{
                        "issue": "Issue description",
                        "recommendation": "How to improve"
                    }}
                ],
                "structure_strengths": [
                    "Strength 1",
                    "Strength 2"
                ]
            }},
            "language_specific_assessment": {{
                "primary_language": "Detected primary language",
                "follows_conventions": true|false,
                "convention_details": "Details about language-specific conventions"
            }}
        }}
        ```
        
        Provide ONLY the JSON response with no additional text. Ensure the JSON is valid.
        """
    
    def _create_final_report_prompt(self, repo_data: Dict, file_analyses: List[Dict], structure_analysis: Dict) -> str:
        """Create a prompt for generating the final comprehensive report"""
        # Prepare a summary of file analyses
        file_analyses_str = json.dumps(file_analyses, indent=2)
        structure_analysis_str = json.dumps(structure_analysis, indent=2)
        
        return f"""
        You are an expert software consultant tasked with creating a comprehensive code quality report.
        
        # Task
        Create a final report summarizing all the analyses performed on this repository. Calculate an overall quality score based on:
        - Code smells (40% weight)
        - Refactoring potential (30% weight)
        - Design pattern implementation (30% weight)
        
        # Repository Information
        - Name: {repo_data["repository"]["name"]}
        - Owner: {repo_data["repository"]["owner"]}
        - URL: {repo_data["repository"]["url"]}
        
        # Analyses Performed
        ## Structure Analysis
        ```json
        {structure_analysis_str}
        ```
        
        ## File Analyses
        ```json
        {file_analyses_str}
        ```
        
        # Response Format
        Provide your report in the following JSON format:
        ```json
        {{
            "repository": {{
                "name": "{repo_data["repository"]["name"]}",
                "owner": "{repo_data["repository"]["owner"]}",
                "url": "{repo_data["repository"]["url"]}"
            }},
            "overall_score": 7.5,
            "summary": "Executive summary of findings",
            "strengths": [
                "Strength 1",
                "Strength 2"
            ],
            "weaknesses": [
                "Weakness 1",
                "Weakness 2"
            ],
            "recommendations": [
                {{
                    "title": "Recommendation title",
                    "description": "Detailed explanation",
                    "priority": "high|medium|low"
                }}
            ],
            "breakdown": {{
                "code_smells_score": 7.0,
                "refactoring_potential_score": 8.0,
                "design_patterns_score": 6.0
            }},
            "top_issues": [
                {{
                    "file": "path/to/file.py",
                    "issue": "Description of the issue",
                    "recommendation": "How to fix it"
                }}
            ]
        }}
        ```
        
        Provide ONLY the JSON response with no additional text. Ensure the JSON is valid.
        """
    
    async def _call_llm(self, prompt: str) -> str:
        """Make an API call to the LLM"""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code analysis AI that provides detailed, accurate assessments of code quality based on software engineering principles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lower temperature for more consistent, analytical responses
                max_tokens=4000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.exception(f"Error calling LLM: {str(e)}")
            raise
    
    def _process_file_analysis_response(self, response: str) -> Dict:
        """Process and validate the LLM's response for file analysis"""
        try:
            # Try to parse the JSON response
            analysis = json.loads(response)
            
            # Validate required fields
            required_fields = ["file_path", "language", "analysis"]
            for field in required_fields:
                if field not in analysis:
                    logger.error(f"Missing required field in LLM response: {field}")
                    analysis[field] = "Unknown" if field != "analysis" else {}
            
            # Ensure analysis contains all expected sub-fields
            if "analysis" in analysis:
                analysis_fields = ["summary", "code_smells", "design_patterns", 
                                  "refactoring_opportunities", "quality_score"]
                for field in analysis_fields:
                    if field not in analysis["analysis"]:
                        logger.warning(f"Missing analysis field in LLM response: {field}")
                        if field in ["code_smells", "design_patterns", "refactoring_opportunities"]:
                            analysis["analysis"][field] = []
                        elif field == "quality_score":
                            analysis["analysis"][field] = 5  # Default mid-range score
                        else:
                            analysis["analysis"][field] = "No information provided"
            
            return {
                "status": "success",
                "data": analysis
            }
            
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON")
            return {
                "status": "error",
                "message": "Failed to parse analysis response",
                "raw_response": response[:500] + "..." if len(response) > 500 else response
            }
        except Exception as e:
            logger.exception(f"Error processing file analysis response: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing analysis: {str(e)}",
                "raw_response": response[:500] + "..." if len(response) > 500 else response
            }
    
    def _process_repository_analysis_response(self, response: str) -> Dict:
        """Process and validate the LLM's response for repository structure analysis"""
        try:
            # Try to parse the JSON response
            analysis = json.loads(response)
            
            # Validate required fields
            required_sections = ["architecture_analysis", "language_specific_assessment"]
            for section in required_sections:
                if section not in analysis:
                    logger.error(f"Missing required section in LLM response: {section}")
                    analysis[section] = {}
            
            return {
                "status": "success",
                "data": analysis
            }
            
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON")
            return {
                "status": "error",
                "message": "Failed to parse structure analysis response",
                "raw_response": response[:500] + "..." if len(response) > 500 else response
            }
        except Exception as e:
            logger.exception(f"Error processing repository analysis response: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing analysis: {str(e)}",
                "raw_response": response[:500] + "..." if len(response) > 500 else response
            }
    
    def _process_final_report_response(self, response: str) -> Dict:
        """Process and validate the LLM's response for the final report"""
        try:
            # Try to parse the JSON response
            report = json.loads(response)
            
            # Validate required fields
            required_fields = ["repository", "overall_score", "summary", "strengths", 
                              "weaknesses", "recommendations", "breakdown", "top_issues"]
            for field in required_fields:
                if field not in report:
                    logger.error(f"Missing required field in final report: {field}")
                    if field in ["strengths", "weaknesses", "recommendations", "top_issues"]:
                        report[field] = []
                    elif field == "breakdown":
                        report[field] = {
                            "code_smells_score": 5.0,
                            "refactoring_potential_score": 5.0,
                            "design_patterns_score": 5.0
                        }
                    elif field == "overall_score":
                        report[field] = 5.0
                    else:
                        report[field] = "No information provided"
            
            # Validate score is within range
            if "overall_score" in report and isinstance(report["overall_score"], (int, float)):
                report["overall_score"] = max(1.0, min(10.0, report["overall_score"]))
            
            return {
                "status": "success",
                "data": report
            }
            
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON")
            return {
                "status": "error",
                "message": "Failed to parse final report response",
                "raw_response": response[:500] + "..." if len(response) > 500 else response
            }
        except Exception as e:
            logger.exception(f"Error processing final report response: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing final report: {str(e)}",
                "raw_response": response[:500] + "..." if len(response) > 500 else response
            }

# Instance to be imported by other modules
llm_service = LLMService()
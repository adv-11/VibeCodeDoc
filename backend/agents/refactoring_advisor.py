import logging
from typing import Dict, List, Any
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

class RefactoringAdvisor:
    """Agent responsible for suggesting refactoring techniques based on code analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define refactoring techniques mapped to code smells
        self.refactoring_techniques = {
            "long_method": [
                {
                    "technique": "Extract Method",
                    "description": "Split the method into smaller, focused methods.",
                    "example": "Extract logical blocks of code into well-named methods that explain their purpose."
                },
                {
                    "technique": "Replace Method with Method Object",
                    "description": "Convert the method into its own class with fields for method parameters and local variables.",
                    "example": "Create a new class named after the method. Pass all local variables as constructor parameters."
                },
                {
                    "technique": "Decompose Conditional",
                    "description": "Extract complex conditional logic into separate methods.",
                    "example": "Replace 'if (complex condition)' with 'if (isValidForOperation())' and implement the condition logic in a separate method."
                }
            ],
            "large_class": [
                {
                    "technique": "Extract Class",
                    "description": "Create new classes to handle distinct responsibilities.",
                    "example": "Identify related methods and fields and move them to a new class with a clear responsibility."
                },
                {
                    "technique": "Extract Interface",
                    "description": "Extract common functionality into interfaces.",
                    "example": "Identify groups of related public methods and extract them into well-defined interfaces."
                },
                {
                    "technique": "Move Method",
                    "description": "Move methods to classes where they are more logically placed.",
                    "example": "If a method uses more features of another class than its own, consider moving it to that class."
                }
            ],
            "long_parameter_list": [
                {
                    "technique": "Introduce Parameter Object",
                    "description": "Replace multiple parameters with a single object.",
                    "example": "Replace method(name, age, address, phone) with method(personDetails) where personDetails is an object."
                },
                {
                    "technique": "Preserve Whole Object",
                    "description": "Pass the whole object instead of multiple attributes.",
                    "example": "Instead of method(customer.getName(), customer.getAddress()), use method(customer)."
                },
                {
                    "technique": "Replace Parameter with Method Call",
                    "description": "If a parameter value can be obtained by a method call, use that instead.",
                    "example": "Replace method(customer, customer.getPlan()) with method(customer) and call getPlan() inside."
                }
            ],
            "duplicate_code": [
                {
                    "technique": "Extract Method",
                    "description": "Extract the duplicated code into a shared method.",
                    "example": "Identify common code blocks and extract them into well-named methods."
                },
                {
                    "technique": "Pull Up Method",
                    "description": "If duplicate code is in subclasses, move it to the superclass.",
                    "example": "When similar methods exist in sibling classes, move them to their parent class."
                },
                {
                    "technique": "Form Template Method",
                    "description": "Define a template method in the superclass that calls abstract methods implemented in subclasses.",
                    "example": "Create a template method in the parent class that defines the algorithm structure, with abstract methods for variant steps."
                }
            ],
            "complex_conditional": [
                {
                    "technique": "Decompose Conditional",
                    "description": "Extract complex conditions into well-named methods.",
                    "example": "Replace 'if (date.before(SUMMER_START) || date.after(SUMMER_END))' with 'if (isWinter(date))'."
                },
                {
                    "technique": "Replace Conditional with Polymorphism",
                    "description": "Create polymorphic objects to handle different cases.",
                    "example": "Replace 'if (type == ENGINEER) { ... } else if (type == MANAGER) { ... }' with specialized classes."
                },
                {
                    "technique": "Replace Nested Conditional with Guard Clauses",
                    "description": "Use guard clauses to handle special cases early.",
                    "example": "Convert nested if-else blocks to 'if (special case) return/throw; // normal execution'."
                }
            ],
            "dead_code": [
                {
                    "technique": "Remove Dead Code",
                    "description": "Simply delete unreachable or never-executed code.",
                    "example": "Delete commented-out code blocks, unreachable code, and unused methods."
                },
                {
                    "technique": "Inline Method",
                    "description": "If a method is only used once, consider inlining it.",
                    "example": "Replace 'result = calculateTemp(); return result;' with 'return calculateTemp();'."
                }
            ],
            "comment_overuse": [
                {
                    "technique": "Rename Method",
                    "description": "Rename methods and variables to better reflect their purpose, reducing the need for comments.",
                    "example": "Replace 'getD()' with 'getDiscount()' and remove the comment explaining it's for discounts."
                },
                {
                    "technique": "Extract Method",
                    "description": "Extract complex logic into well-named methods that serve as self-documentation.",
                    "example": "Replace a complex algorithm with a call to a descriptively named method."
                },
                {
                    "technique": "Introduce Assertion",
                    "description": "Replace comments about assumptions with assertions.",
                    "example": "Replace '// x must be positive' with 'assert x > 0'."
                }
            ]
        }

    async def suggest_refactorings(self, file_path: str, file_content: str, analysis_results: Dict) -> Dict:
        """Suggest refactoring techniques based on analysis results"""
        try:
            # Extract code smells from analysis results
            code_smells = analysis_results.get("data", {}).get("analysis", {}).get("code_smells", [])
            
            # Generate refactoring suggestions
            refactoring_suggestions = self._generate_refactoring_suggestions(code_smells)
            
            # Enhance suggestions with LLM insights
            enhanced_suggestions = await self._enhance_suggestions_with_llm(file_path, file_content, code_smells, refactoring_suggestions)
            
            return {
                "status": "success",
                "file_path": file_path,
                "refactoring_suggestions": enhanced_suggestions
            }
            
        except Exception as e:
            self.logger.exception(f"Error generating refactoring suggestions for {file_path}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error generating refactoring suggestions: {str(e)}",
                "file_path": file_path
            }
    
    def _generate_refactoring_suggestions(self, code_smells: List[Dict]) -> List[Dict]:
        """Generate initial refactoring suggestions based on detected code smells"""
        suggestions = []
        
        for smell in code_smells:
            smell_type = smell.get("type")
            
            # Get appropriate refactoring techniques for this smell type
            if smell_type in self.refactoring_techniques:
                techniques = self.refactoring_techniques[smell_type]
                
                for technique in techniques:
                    suggestion = {
                        "smell_type": smell_type,
                        "smell_description": smell.get("description", ""),
                        "affected_area": smell.get("lines", ""),
                        "technique": technique["technique"],
                        "description": technique["description"],
                        "example": technique["example"],
                        "severity": smell.get("severity", "medium")
                    }
                    suggestions.append(suggestion)
            else:
                # For unknown smell types, add a generic suggestion
                suggestions.append({
                    "smell_type": smell_type,
                    "smell_description": smell.get("description", ""),
                    "affected_area": smell.get("lines", ""),
                    "technique": "Refactor based on best practices",
                    "description": "Consider refactoring this code using standard techniques.",
                    "example": "Review the code for clarity, simplicity, and maintainability.",
                    "severity": smell.get("severity", "medium")
                })
        
        return suggestions
    
    async def _enhance_suggestions_with_llm(self, file_path: str, file_content: str, code_smells: List[Dict], initial_suggestions: List[Dict]) -> List[Dict]:
        """Enhance refactoring suggestions using LLM for more context-aware advice"""
        try:
            # Skip LLM enhancement if there are no code smells or suggestions
            if not code_smells or not initial_suggestions:
                return initial_suggestions
            
            # Prepare the prompt for the LLM
            prompt = self._create_enhancement_prompt(file_path, file_content, code_smells, initial_suggestions)
            
            # Call the LLM service
            llm_response = await llm_service._call_llm(prompt)
            
            # Process the LLM response
            enhanced_suggestions = self._process_llm_enhancement_response(llm_response, initial_suggestions)
            
            return enhanced_suggestions
            
        except Exception as e:
            self.logger.exception(f"Error enhancing suggestions with LLM for {file_path}: {str(e)}")
            # Return initial suggestions if LLM enhancement fails
            return initial_suggestions
    
    def _create_enhancement_prompt(self, file_path: str, file_content: str, code_smells: List[Dict], initial_suggestions: List[Dict]) -> str:
        """Create a prompt for the LLM to enhance refactoring suggestions"""
        # Convert initial suggestions to a string representation
        suggestions_str = "\n".join([
            f"- {s['technique']} for {s['smell_type']} at {s['affected_area']}: {s['description']}"
            for s in initial_suggestions
        ])
        
        # Create a list of code smells for the prompt
        smells_str = "\n".join([
            f"- {smell.get('type')}: {smell.get('description')} at {smell.get('lines')} (Severity: {smell.get('severity', 'medium')})"
            for smell in code_smells
        ])
        
        return f"""
        You are an expert software refactoring advisor. Your task is to enhance the following refactoring suggestions 
        with more context-specific advice based on the actual code.
        
        # File Information
        - Path: {file_path}
        
        # Code Content
        ```
        {file_content}
        ```
        
        # Detected Code Smells
        {smells_str}
        
        # Initial Refactoring Suggestions
        {suggestions_str}
        
        # Task
        For each refactoring suggestion:
        1. Provide a more context-specific application of the technique
        2. Add a code example showing how the refactoring could be applied to this specific file
        3. Assess the potential impact (high, medium, low) of applying this refactoring
        4. Identify any dependencies or related refactorings that should be applied together
        
        # Response Format
        Provide your enhanced suggestions in the following JSON format:
        ```json
        [
            {{
                "smell_type": "original smell type",
                "technique": "original technique",
                "specific_application": "context-specific description",
                "code_example": "specific code example for this file",
                "impact": "high|medium|low",
                "related_refactorings": ["related technique 1", "related technique 2"],
                "affected_area": "original affected area",
                "severity": "original severity"
            }}
        ]
        ```
        
        Ensure your response contains valid JSON with only the enhanced suggestions array and no additional text.
        """
    
    def _process_llm_enhancement_response(self, llm_response: str, initial_suggestions: List[Dict]) -> List[Dict]:
        """Process the LLM response to extract enhanced suggestions"""
        try:
            import json
            import re
            
            # Try to extract JSON from the response
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', llm_response)
            if json_match:
                json_str = json_match.group(1)
            else:
                # If no JSON block is found, try to parse the whole response
                json_str = llm_response
            
            # Parse the JSON
            enhanced_data = json.loads(json_str)
            
            # Validate and merge with initial suggestions
            enhanced_suggestions = []
            
            # Create a mapping of initial suggestions for easy lookup
            suggestion_map = {}
            for suggestion in initial_suggestions:
                key = f"{suggestion['smell_type']}:{suggestion['technique']}"
                suggestion_map[key] = suggestion
            
            # Process enhanced suggestions
            for enhanced in enhanced_data:
                smell_type = enhanced.get("smell_type")
                technique = enhanced.get("technique")
                
                # Find corresponding initial suggestion
                key = f"{smell_type}:{technique}"
                original = suggestion_map.get(key)
                
                if original:
                    # Merge the original with enhanced data
                    merged = {**original}  # Create a copy of the original
                    
                    # Add enhanced fields
                    merged["specific_application"] = enhanced.get("specific_application", merged.get("description", ""))
                    merged["code_example"] = enhanced.get("code_example", merged.get("example", ""))
                    merged["impact"] = enhanced.get("impact", "medium")
                    merged["related_refactorings"] = enhanced.get("related_refactorings", [])
                    
                    enhanced_suggestions.append(merged)
                else:
                    # If no matching original suggestion, add the enhanced one directly
                    enhanced_suggestions.append({
                        "smell_type": smell_type,
                        "smell_description": enhanced.get("smell_description", ""),
                        "affected_area": enhanced.get("affected_area", ""),
                        "technique": technique,
                        "description": enhanced.get("description", ""),
                        "example": enhanced.get("example", ""),
                        "specific_application": enhanced.get("specific_application", ""),
                        "code_example": enhanced.get("code_example", ""),
                        "impact": enhanced.get("impact", "medium"),
                        "related_refactorings": enhanced.get("related_refactorings", []),
                        "severity": enhanced.get("severity", "medium")
                    })
            
            # If no valid enhancements were found, return the initial suggestions
            if not enhanced_suggestions:
                return initial_suggestions
                
            return enhanced_suggestions
            
        except Exception as e:
            self.logger.exception(f"Error processing LLM enhancement response: {str(e)}")
            # Return the initial suggestions if processing fails
            return initial_suggestions
    
    async def generate_refactoring_guide(self, file_path: str, suggestions: List[Dict]) -> Dict:
        """Generate a comprehensive refactoring guide for a file based on suggestions"""
        try:
            # Skip if there are no suggestions
            if not suggestions:
                return {
                    "status": "success",
                    "file_path": file_path,
                    "guide": {
                        "title": f"Refactoring Guide for {file_path}",
                        "summary": "No refactoring suggestions were identified for this file.",
                        "steps": []
                    }
                }
            
            # Group suggestions by severity
            high_priority = [s for s in suggestions if s.get("severity") == "high"]
            medium_priority = [s for s in suggestions if s.get("severity") == "medium"]
            low_priority = [s for s in suggestions if s.get("severity") == "low"]
            
            # Create a refactoring plan
            refactoring_steps = []
            
            # First add high priority refactorings
            for i, suggestion in enumerate(high_priority, 1):
                refactoring_steps.append({
                    "step": i,
                    "title": f"Apply {suggestion['technique']} to address {suggestion['smell_type']}",
                    "description": suggestion.get("specific_application", suggestion.get("description", "")),
                    "code_example": suggestion.get("code_example", suggestion.get("example", "")),
                    "priority": "high",
                    "affected_area": suggestion.get("affected_area", ""),
                    "related_steps": self._find_related_step_numbers(suggestion, suggestions)
                })
            
            # Then medium priority
            for i, suggestion in enumerate(medium_priority, len(high_priority) + 1):
                refactoring_steps.append({
                    "step": i,
                    "title": f"Apply {suggestion['technique']} to address {suggestion['smell_type']}",
                    "description": suggestion.get("specific_application", suggestion.get("description", "")),
                    "code_example": suggestion.get("code_example", suggestion.get("example", "")),
                    "priority": "medium",
                    "affected_area": suggestion.get("affected_area", ""),
                    "related_steps": self._find_related_step_numbers(suggestion, suggestions)
                })
            
            # Finally low priority
            for i, suggestion in enumerate(low_priority, len(high_priority) + len(medium_priority) + 1):
                refactoring_steps.append({
                    "step": i,
                    "title": f"Apply {suggestion['technique']} to address {suggestion['smell_type']}",
                    "description": suggestion.get("specific_application", suggestion.get("description", "")),
                    "code_example": suggestion.get("code_example", suggestion.get("example", "")),
                    "priority": "low",
                    "affected_area": suggestion.get("affected_area", ""),
                    "related_steps": self._find_related_step_numbers(suggestion, suggestions)
                })
            
            # Create a summary
            summary = f"This guide contains {len(refactoring_steps)} refactoring steps: " \
                      f"{len(high_priority)} high priority, {len(medium_priority)} medium priority, " \
                      f"and {len(low_priority)} low priority refactorings."
            
            if high_priority:
                summary += f" Focus first on addressing the {len(high_priority)} high priority issues."
            
            # Return the complete guide
            return {
                "status": "success",
                "file_path": file_path,
                "guide": {
                    "title": f"Refactoring Guide for {file_path}",
                    "summary": summary,
                    "steps": refactoring_steps
                }
            }
            
        except Exception as e:
            self.logger.exception(f"Error generating refactoring guide for {file_path}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error generating refactoring guide: {str(e)}",
                "file_path": file_path
            }
    
    def _find_related_step_numbers(self, current_suggestion: Dict, all_suggestions: List[Dict]) -> List[int]:
        """Find steps related to the current suggestion"""
        related_steps = []
        
        # If the suggestion has explicitly defined related refactorings
        related_techniques = current_suggestion.get("related_refactorings", [])
        
        # Find techniques that are related
        for i, suggestion in enumerate(all_suggestions, 1):
            # Skip the current suggestion
            if suggestion is current_suggestion:
                continue
                
            # Check if this suggestion's technique is in the related techniques list
            if suggestion["technique"] in related_techniques:
                related_steps.append(i)
                
            # Check if they affect the same area
            elif suggestion.get("affected_area") == current_suggestion.get("affected_area") and suggestion.get("affected_area"):
                related_steps.append(i)
                
            # Check if they address the same smell type
            elif suggestion.get("smell_type") == current_suggestion.get("smell_type"):
                related_steps.append(i)
        
        return related_steps

# Create an instance to be imported by other modules
refactoring_advisor = RefactoringAdvisor()
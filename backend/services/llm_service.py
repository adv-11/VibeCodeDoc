import os
import json
from typing import List, Dict, Any, Optional
import openai
from config.settings import settings

class LLMService:
    def __init__(self, api_key: str = settings.OPENAI_API_KEY, model: str = settings.LLM_MODEL):
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key
    
    async def analyze_code(self, code: str, context: str, max_tokens: int = 1000) -> str:
        """Analyze code with the LLM and return insights"""
        prompt = f"""
        Context: {context}
        
        Code to analyze:
        ```
        {code}
        ```
        
        Provide analysis of this code based on the context given.
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code analysis assistant with expertise in software design, architecture, and best practices."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            return f"Analysis failed: {str(e)}"
    
    async def identify_design_patterns(self, code_snippets: Dict[str, str]) -> List[Dict[str, Any]]:
        """Identify design patterns in code snippets"""
        files_json = json.dumps({k: v[:1000] for k, v in code_snippets.items()})  # Truncate for API limits
        
        prompt = f"""
        Analyze these code files to identify design patterns:
        {files_json}
        
        Return a JSON array of design patterns found, with format:
        [
          {{
            "name": "PATTERN_NAME",
            "files": ["file/path1", "file/path2"],
            "confidence": 0.9,
            "description": "Description of how the pattern is implemented"
          }}
        ]
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code analysis assistant specialized in identifying design patterns."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.2
            )
            
            result = response.choices[0].message.content
            # Extract JSON from the response
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # If JSON extraction fails, try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result)
                if json_match:
                    return json.loads(json_match.group(1))
                return []
        except Exception as e:
            print(f"Error in design pattern identification: {str(e)}")
            return []
    
    async def detect_code_smells(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Detect code smells in a single file"""
        prompt = f"""
        Analyze this code for code smells:
        File: {file_path}
        
        ```
        {code}
        ```
        
        Return a JSON array of code smells found, with format:
        [
          {{
            "type": "SMELL_TYPE",
            "description": "Description of the smell",
            "file_path": "{file_path}",
            "line_start": 12,
            "line_end": 18,
            "severity": "high/medium/low",
            "recommendation": "How to fix it"
          }}
        ]
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code quality analyst who identifies code smells and provides actionable recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.2
            )
            
            result = response.choices[0].message.content
            # Extract JSON from the response
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # If JSON extraction fails, try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result)
                if json_match:
                    return json.loads(json_match.group(1))
                return []
        except Exception as e:
            print(f"Error in code smell detection: {str(e)}")
            return []
    
    async def suggest_refactoring(self, code_smells: List[Dict[str, Any]], file_content: str) -> List[Dict[str, Any]]:
        """Suggest refactoring based on detected code smells"""
        smells_json = json.dumps(code_smells)
        
        prompt = f"""
        Based on these code smells:
        {smells_json}
        
        And this file content:
        ```
        {file_content[:2000]}  # Truncated for API limits
        ```
        
        Suggest refactoring solutions in JSON format:
        [
          {{
            "type": "REFACTORING_TYPE",
            "description": "Description of the refactoring",
            "file_paths": ["file/path"],
            "before_snippet": "Problem code",
            "after_snippet": "Improved code",
            "rationale": "Why this improves the code",
            "priority": "high/medium/low"
          }}
        ]
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a refactoring expert who provides concrete, actionable refactoring suggestions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.2
            )
            
            result = response.choices[0].message.content
            # Extract JSON from the response
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # If JSON extraction fails, try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result)
                if json_match:
                    return json.loads(json_match.group(1))
                return []
        except Exception as e:
            print(f"Error in refactoring suggestion: {str(e)}")
            return []
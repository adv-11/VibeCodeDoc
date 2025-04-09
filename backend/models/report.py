from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from models.analysis import StructuralAnalysis, DesignPattern, CodeSmell, RefactoringSuggestion

class ReportSummary(BaseModel):
    overall_quality_score: float  # 0-100
    primary_strengths: List[str]
    primary_concerns: List[str]
    improvement_priorities: List[str]

class ReportSection(BaseModel):
    title: str
    content: str
    subsections: List['ReportSection'] = []

class Report(BaseModel):
    id: str
    repository_id: str
    analysis_id: str
    created_at: datetime = datetime.now()
    summary: ReportSummary
    structural_analysis: StructuralAnalysis
    design_patterns: List[DesignPattern] = []
    code_smells: List[CodeSmell] = []
    refactoring_suggestions: List[RefactoringSuggestion] = []
    detailed_sections: List[ReportSection] = []
    
    class Config:
        schema_extra = {
            "example": {
                "id": "report-123",
                "repository_id": "repo-456",
                "analysis_id": "analysis-789",
                "created_at": "2023-09-15T12:30:45",
                "summary": {
                    "overall_quality_score": 75.5,
                    "primary_strengths": ["Clean architecture", "Good test coverage"],
                    "primary_concerns": ["High coupling in core modules", "Inconsistent error handling"],
                    "improvement_priorities": ["Refactor core module interfaces", "Standardize error handling"]
                }
            }
        }
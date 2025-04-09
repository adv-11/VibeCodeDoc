from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class CodeSmell(BaseModel):
    type: str
    description: str
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    severity: str
    recommendation: str

class DesignPattern(BaseModel):
    name: str
    files: List[str]
    confidence: float
    description: str

class RefactoringSuggestion(BaseModel):
    type: str
    description: str
    file_paths: List[str]
    before_snippet: Optional[str] = None
    after_snippet: Optional[str] = None
    rationale: str
    priority: str

class StructuralAnalysis(BaseModel):
    file_count: int
    directory_count: int
    language_breakdown: Dict[str, float]
    complexity_metrics: Dict[str, Any]
    dependency_graph: Optional[Dict[str, List[str]]] = None

class Analysis(BaseModel):
    id: str
    repository_id: str
    status: AnalysisStatus = AnalysisStatus.PENDING
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    structural_analysis: Optional[StructuralAnalysis] = None
    design_patterns: List[DesignPattern] = []
    code_smells: List[CodeSmell] = []
    refactoring_suggestions: List[RefactoringSuggestion] = []
    error: Optional[str] = None
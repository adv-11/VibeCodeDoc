# backend/models/analysis.py
from typing import Dict, List, Optional

class RepositoryAnalysis:
    """Represents the analysis of a repository."""

    def __init__(self, repository: Dict, structure_analysis: Dict, file_analyses: List[Dict], final_report: Dict, execution_time: float):
        self.repository = repository
        self.structure_analysis = structure_analysis
        self.file_analyses = file_analyses
        self.final_report = final_report
        self.execution_time = execution_time

    def __repr__(self):
        return f"RepositoryAnalysis(repository={self.repository}, structure_analysis={self.structure_analysis}, file_analyses={self.file_analyses}, final_report={self.final_report}, execution_time={self.execution_time})"

    def to_dict(self):
        return {
            "repository": self.repository,
            "structure_analysis": self.structure_analysis,
            "file_analyses": self.file_analyses,
            "final_report": self.final_report,
            "execution_time": self.execution_time
        }
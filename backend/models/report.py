# backend/models/report.py
from typing import Dict, List, Optional

class AnalysisReport:
    """Represents the final report of the code analysis."""

    def __init__(self, repository: Dict, overall_score: float, summary: str, strengths: List[str], weaknesses: List[str], recommendations: List[Dict], breakdown: Dict, top_issues: List[Dict]):
        self.repository = repository
        self.overall_score = overall_score
        self.summary = summary
        self.strengths = strengths
        self.weaknesses = weaknesses
        self.recommendations = recommendations
        self.breakdown = breakdown
        self.top_issues = top_issues

    def __repr__(self):
        return f"AnalysisReport(repository={self.repository}, overall_score={self.overall_score}, summary='{self.summary}', strengths={self.strengths}, weaknesses={self.weaknesses}, recommendations={self.recommendations}, breakdown={self.breakdown}, top_issues={self.top_issues})"

    def to_dict(self):
        return {
            "repository": self.repository,
            "overall_score": self.overall_score,
            "summary": self.summary,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": self.recommendations,
            "breakdown": self.breakdown,
            "top_issues": self.top_issues
        }
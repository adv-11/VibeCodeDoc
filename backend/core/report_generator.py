import logging
import json
from typing import Dict, List, Any, Optional
import os
import time
from datetime import datetime

from models.repository import Repository
from models.analysis import RepositoryAnalysis
from models.report import Report, ReportFormat

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates reports based on code analysis results"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.output_dir = os.environ.get("REPORT_OUTPUT_DIR", "reports")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def generate_report(self, analysis: RepositoryAnalysis, format: ReportFormat = ReportFormat.JSON) -> Report:
        """Generate a report based on analysis results"""
        try:
            report_id = f"{analysis.repository['name']}_{int(time.time())}"
            
            # Generate appropriate content based on the requested format
            if format == ReportFormat.JSON:
                content = await self._generate_json_report(analysis)
                filename = f"{report_id}.json"
            elif format == ReportFormat.HTML:
                content = await self._generate_html_report(analysis)
                filename = f"{report_id}.html"
            elif format == ReportFormat.MARKDOWN:
                content = await self._generate_markdown_report(analysis)
                filename = f"{report_id}.md"
            else:
                raise ValueError(f"Unsupported report format: {format}")
            
            # Save the report to a file
            file_path = os.path.join(self.output_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return Report(
                id=report_id,
                repository_name=analysis.repository["name"],
                repository_owner=analysis.repository["owner"],
                timestamp=datetime.now().isoformat(),
                format=format,
                file_path=file_path,
                content=content
            )
            
        except Exception as e:
            self.logger.exception(f"Error generating report: {str(e)}")
            raise
    
    async def _generate_json_report(self, analysis: RepositoryAnalysis) -> str:
        """Generate a JSON report"""
        report_data = {
            "repository": analysis.repository,
            "summary": analysis.final_report.get("summary", ""),
            "overall_score": analysis.final_report.get("overall_score", 0),
            "execution_time": analysis.execution_time,
            "timestamp": datetime.now().isoformat(),
            "structure_analysis": analysis.structure_analysis,
            "pattern_analysis": analysis.pattern_analysis,
            "breakdown": analysis.final_report.get("breakdown", {}),
            "strengths": analysis.final_report.get("strengths", []),
            "weaknesses": analysis.final_report.get("weaknesses", []),
            "recommendations": analysis.final_report.get("recommendations", []),
            "top_issues": analysis.final_report.get("top_issues", []),
            "file_analyses": [
                {
                    "file_path": file.file_path,
                    "file_name": file.file_name,
                    "file_extension": file.file_extension,
                    "quality_score": file.llm_analysis.get("analysis", {}).get("quality_score", 0),
                    "summary": file.llm_analysis.get("analysis", {}).get("summary", ""),
                    "smells": file.smells,
                    "patterns": file.patterns,
                    "refactoring_suggestions": file.refactoring_suggestions,
                    "refactoring_guide": file.refactoring_guide
                }
                for file in analysis.file_analyses
            ]
        }
        
        return json.dumps(report_data, indent=2)
    
    async def _generate_html_report(self, analysis: RepositoryAnalysis) -> str:
        """Generate an HTML report"""
        # Convert analysis data to JSON for embedding in HTML
        analysis_json = json.dumps({
            "repository": analysis.repository,
            "final_report": analysis.final_report,
            "structure_analysis": analysis.structure_analysis,
            "pattern_analysis": analysis.pattern_analysis,
            "file_analyses": [file.model_dump() for file in analysis.file_analyses],
            "execution_time": analysis.execution_time,
            "timestamp": datetime.now().isoformat()
        })
        
        # Create an HTML template with embedded data and a simple UI
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Analysis Report - {analysis.repository["name"]}</title>
    <style>
        :root {{
            --primary-color: #4a6cb3;
            --secondary-color: #6c8cd5;
            --accent-color: #ff6b6b;
            --text-color: #333;
            --background-color: #f9f9f9;
            --card-color: #ffffff;
            --border-color: #e1e4e8;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--background-color);
            margin: 0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        h1, h2, h3, h4 {{
            margin-top: 0;
            color: var(--primary-color);
        }}
        
        .card {{
            background-color: var(--card-color);
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
        }}
        
        .summary-card {{
            background-color: var(--primary-color);
            color: white;
        }}
        
        .summary-card h2 {{
            color: white;
        }}
        
        .score {{
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            margin: 20px 0 auto;;
        }}
        
        .score span {{
            font-size: 24px;
            color: var(--secondary-color);
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section h2 {{
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        table th, table td {{
            border: 1px solid var(--border-color);
            padding: 10px;
            text-align: left;
        }}
        
        table th {{
            background-color: var(--primary-color);
            color: white;
        }}
        
        table tr:nth-child(even) {{
            background-color: var(--background-color);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Code Analysis Report</h1>
            <h2>{analysis.repository["name"]}</h2>
        </header>
        
        <div class="card summary-card">
            <h2>Summary</h2>
            <p>{analysis.final_report.get("summary", "No summary available.")}</p>
            <div class="score">
                {analysis.final_report.get("overall_score", 0)}
                <span>/ 10</span>
            </div>
        </div>
        
        <div class="section">
            <h2>Strengths</h2>
            <ul>
                {"".join(f"<li>{strength}</li>" for strength in analysis.final_report.get("strengths", []))}
            </ul>
        </div>
        
        <div class="section">
            <h2>Weaknesses</h2>
            <ul>
                {"".join(f"<li>{weakness}</li>" for weakness in analysis.final_report.get("weaknesses", []))}
            </ul>
        </div>
        
        <div class="section">
            <h2>Recommendations</h2>
            <ul>
                {"".join(f"<li>{rec['title']}: {rec['description']} (Priority: {rec['priority']})</li>" for rec in analysis.final_report.get("recommendations", []))}
            </ul>
        </div>
        
        <div class="section">
            <h2>Top Issues</h2>
            <table>
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Issue</th>
                        <th>Recommendation</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(f"<tr><td>{issue['file']}</td><td>{issue['issue']}</td><td>{issue['recommendation']}</td></tr>" for issue in analysis.final_report.get('top_issues', []))}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    async def _generate_markdown_report(self, analysis: RepositoryAnalysis) -> str:
        """Generate a Markdown report"""
        markdown = f"# Code Analysis Report - {analysis.repository['name']}\n\n"
        markdown += f"**Summary:** {analysis.final_report.get('summary', 'No summary available.')}\n\n"
        markdown += f"**Overall Score:** {analysis.final_report.get('overall_score', 0)} / 10\n\n"
        
        markdown += "## Strengths\n"
        markdown += "\n".join(f"- {strength}" for strength in analysis.final_report.get("strengths", [])) + "\n\n"
        
        markdown += "## Weaknesses\n"
        markdown += "\n".join(f"- {weakness}" for weakness in analysis.final_report.get("weaknesses", [])) + "\n\n"
        
        markdown += "## Recommendations\n"
        for rec in analysis.final_report.get("recommendations", []):
            markdown += f"- **{rec['title']}**: {rec['description']} (Priority: {rec['priority']})\n"
        
        markdown += "\n## Top Issues\n"
        markdown += "| File | Issue | Recommendation |\n"
        markdown += "|------|-------|----------------|\n"
        for issue in analysis.final_report.get("top_issues", []):
            markdown += f"| {issue['file']} | {issue['issue']} | {issue['recommendation']} |\n"
        
        return markdown
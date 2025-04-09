
from typing import List, Dict, Any
import statistics

from models.analysis import Analysis
from models.repository import Repository
from models.report import Report, ReportSummary, ReportSection

async def generate_report(analysis: Analysis, repository: Repository) -> Report:
    """Generate a comprehensive report from analysis results"""
    
    # Generate summary
    summary = await generate_summary(analysis)
    
    # Create detailed sections
    detailed_sections = await generate_detailed_sections(analysis, repository)
    
    # Create report
    report = Report(
        id="temp",  # Will be replaced by caller
        repository_id=repository.id,
        analysis_id=analysis.id,
        summary=summary,
        structural_analysis=analysis.structural_analysis,
        design_patterns=analysis.design_patterns,
        code_smells=analysis.code_smells,
        refactoring_suggestions=analysis.refactoring_suggestions,
        detailed_sections=detailed_sections
    )
    
    return report

async def generate_summary(analysis: Analysis) -> ReportSummary:
    """Generate a summary of the analysis results"""
    
    # Calculate quality score
    quality_score = await calculate_quality_score(analysis)
    
    # Extract primary strengths
    strengths = await identify_strengths(analysis)
    
    # Extract primary concerns
    concerns = await identify_concerns(analysis)
    
    # Determine improvement priorities
    priorities = await determine_priorities(analysis)
    
    return ReportSummary(
        overall_quality_score=quality_score,
        primary_strengths=strengths,
        primary_concerns=concerns,
        improvement_priorities=priorities
    )

async def calculate_quality_score(analysis: Analysis) -> float:
    """Calculate an overall quality score for the codebase"""
    base_score = 70.0  # Start with a neutral score
    
    # Deduct for code smells based on severity
    if analysis.code_smells:
        severity_weights = {"high": 3.0, "medium": 1.5, "low": 0.5}
        smell_deduction = sum(
            severity_weights.get(smell.severity, 1.0) 
            for smell in analysis.code_smells
        )
        # Normalize deduction (max 30 points)
        normalized_deduction = min(30.0, smell_deduction / (len(analysis.code_smells) / 3))
        base_score -= normalized_deduction
    
    # Add points for good design patterns
    if analysis.design_patterns:
        pattern_bonus = min(15.0, len(analysis.design_patterns) * 2.5)
        base_score += pattern_bonus
    
    # Adjust based on structural metrics if available
    if analysis.structural_analysis and hasattr(analysis.structural_analysis, 'complexity_metrics'):
        complexity = analysis.structural_analysis.complexity_metrics.get('average_complexity', 5)
        if complexity < 5:  # Lower complexity is better
            base_score += (5 - complexity) * 2
        else:
            base_score -= (complexity - 5) * 2
    
    # Ensure score is within 0-100 range
    return max(0.0, min(100.0, round(base_score, 1)))

async def identify_strengths(analysis: Analysis) -> List[str]:
    """Identify primary strengths of the codebase"""
    strengths = []
    
    # Check for design patterns
    if analysis.design_patterns:
        strengths.append(f"Implements {len(analysis.design_patterns)} recognized design patterns")
    
    # Check for low code smell count
    if not analysis.code_smells or len(analysis.code_smells) < 5:
        strengths.append("Low number of code smells detected")
    
    # Check language diversity/consistency
    if analysis.structural_analysis and analysis.structural_analysis.language_breakdown:
        lang_breakdown = analysis.structural_analysis.language_breakdown
        # If primary language is > 80%, it's consistent
        primary_lang = next(iter(lang_breakdown.items()), (None, 0))
        if primary_lang[1] > 80:
            strengths.append(f"Consistent use of {primary_lang[0]} throughout the codebase")
        # If multiple languages > 20%, it's diverse
        elif sum(1 for _, pct in lang_breakdown.items() if pct > 20) > 1:
            strengths.append("Good polyglot architecture with multiple languages")
    
    # Check for modular structure
    if analysis.structural_analysis and hasattr(analysis.structural_analysis, 'directory_count'):
        if analysis.structural_analysis.directory_count > 5:
            strengths.append("Well-organized modular structure")
    
    # Add default strength if none found
    if not strengths:
        strengths.append("Clean and readable code structure")
    
    return strengths[:3]  # Return top 3 strengths

async def identify_concerns(analysis: Analysis) -> List[str]:
    """Identify primary concerns in the codebase"""
    concerns = []
    
    # Check for high severity code smells
    high_severity_smells = [s for s in analysis.code_smells if s.severity == "high"]
    if high_severity_smells:
        smell_types = set(s.type for s in high_severity_smells)
        if len(smell_types) > 1:
            concerns.append(f"Multiple high-severity code issues including {', '.join(list(smell_types)[:2])}")
        else:
            concerns.append(f"High-severity {next(iter(smell_types))} issues")
    
    # Check code complexity
    if (analysis.structural_analysis and hasattr(analysis.structural_analysis, 'complexity_metrics') and 
        analysis.structural_analysis.complexity_metrics.get('average_complexity', 0) > 7):
        concerns.append("High average code complexity")
    
    # Check for lack of design patterns
    if not analysis.design_patterns:
        concerns.append("Limited use of established design patterns")
    
    # Check for excessive file count
    if analysis.structural_analysis and hasattr(analysis.structural_analysis, 'file_count'):
        if analysis.structural_analysis.file_count > 200:
            concerns.append("Large codebase with potential maintainability challenges")
    
    # Add default concern if none found
    if not concerns and analysis.code_smells:
        most_common_smell = max(
            set(s.type for s in analysis.code_smells), 
            key=lambda x: sum(1 for s in analysis.code_smells if s.type == x)
        )
        concerns.append(f"Several instances of {most_common_smell}")
    elif not concerns:
        concerns.append("Limited documentation and comments")
    
    return concerns[:3]  # Return top 3 concerns

async def determine_priorities(analysis: Analysis) -> List[str]:
    """Determine improvement priorities based on analysis"""
    
    # Start with refactoring suggestions if available
    priorities = []
    
    # Add high priority refactorings
    high_priority_refactorings = [r for r in analysis.refactoring_suggestions if r.priority == "high"]
    if high_priority_refactorings:
        refactoring_types = set(r.type for r in high_priority_refactorings)
        if len(refactoring_types) > 1:
            priorities.append(f"Address high-priority refactorings: {', '.join(list(refactoring_types)[:2])}")
        else:
            priorities.append(f"Focus on {next(iter(refactoring_types))} refactoring")
    
    # Add suggestion based on highest severity code smells
    if analysis.code_smells:
        worst_smells = sorted(analysis.code_smells, key=lambda s: {"high": 3, "medium": 2, "low": 1}.get(s.severity, 0), reverse=True)
        if worst_smells:
            worst_smell = worst_smells[0]
            priorities.append(f"Fix {worst_smell.type} issues in {worst_smell.file_path}")
    
    # Suggest implementing design patterns if none detected
    if not analysis.design_patterns:
        priorities.append("Implement appropriate design patterns for better maintainability")
    
    # Suggest code organization improvements based on structural analysis
    if analysis.structural_analysis:
        if hasattr(analysis.structural_analysis, 'complexity_metrics') and analysis.structural_analysis.complexity_metrics.get('average_complexity', 0) > 5:
            priorities.append("Reduce code complexity through decomposition and refactoring")
    
    # Add generic priorities if needed
    if len(priorities) < 3:
        general_priorities = [
            "Improve test coverage and test quality",
            "Enhance documentation and code comments",
            "Standardize coding style across the codebase"
        ]
        priorities.extend(general_priorities)
    
    return priorities[:3]  # Return top 3 priorities

async def generate_detailed_sections(analysis: Analysis, repository: Repository) -> List[ReportSection]:
    """Generate detailed report sections"""
    sections = []
    
    # Introduction section
    intro_section = ReportSection(
        title="Introduction",
        content=f"This report presents an analysis of the repository at {repository.url}, "
                f"branch '{repository.branch}'. The analysis was performed on the code "
                f"structure, design patterns, code quality, and potential improvements."
    )
    sections.append(intro_section)
    
    # Code structure section
    if analysis.structural_analysis:
        structure_content = (
            f"The repository contains {analysis.structural_analysis.file_count} files "
            f"across {analysis.structural_analysis.directory_count} directories. "
        )
        
        # Add language breakdown
        if analysis.structural_analysis.language_breakdown:
            lang_list = [f"{lang}: {pct}%" for lang, pct in 
                       list(analysis.structural_analysis.language_breakdown.items())[:3]]
            structure_content += f"Primary languages used are {', '.join(lang_list)}."
        
        # Add complexity info
        if hasattr(analysis.structural_analysis, 'complexity_metrics'):
            complexity = analysis.structural_analysis.complexity_metrics.get('average_complexity', 'N/A')
            structure_content += f" Average code complexity is {complexity}."
            
        structure_section = ReportSection(
            title="Code Structure",
            content=structure_content
        )
        sections.append(structure_section)
    
    # Design patterns section
    if analysis.design_patterns:
        patterns_content = f"The analysis identified {len(analysis.design_patterns)} design patterns in the codebase:"
        
        pattern_subsections = []
        for pattern in analysis.design_patterns:
            pattern_section = ReportSection(
                title=pattern.name,
                content=(
                    f"{pattern.description}\n\n"
                    f"Identified in files: {', '.join(pattern.files)}\n"
                    f"Confidence: {pattern.confidence * 100:.1f}%"
                )
            )
            pattern_subsections.append(pattern_section)
            
        patterns_section = ReportSection(
            title="Design Patterns",
            content=patterns_content,
            subsections=pattern_subsections
        )
        sections.append(patterns_section)
    
    # Code smells section
    if analysis.code_smells:
        smells_by_severity = {
            "high": [s for s in analysis.code_smells if s.severity == "high"],
            "medium": [s for s in analysis.code_smells if s.severity == "medium"],
            "low": [s for s in analysis.code_smells if s.severity == "low"]
        }
        
        smells_content = (
            f"The analysis detected {len(analysis.code_smells)} code smells: "
            f"{len(smells_by_severity['high'])} high severity, "
            f"{len(smells_by_severity['medium'])} medium severity, and "
            f"{len(smells_by_severity['low'])} low severity."
        )
        
        smell_subsections = []
        for severity in ["high", "medium", "low"]:
            if smells_by_severity[severity]:
                severity_content = ""
                for smell in smells_by_severity[severity][:5]:  # Top 5 per severity
                    severity_content += (
                        f"- **{smell.type}** in {smell.file_path}"
                        f"{f' (lines {smell.line_start}-{smell.line_end})' if smell.line_start else ''}: "
                        f"{smell.description}. {smell.recommendation}\n\n"
                    )
                
                if len(smells_by_severity[severity]) > 5:
                    severity_content += f"... and {len(smells_by_severity[severity]) - 5} more."
                    
                severity_section = ReportSection(
                    title=f"{severity.capitalize()} Severity Issues",
                    content=severity_content
                )
                smell_subsections.append(severity_section)
        
        smells_section = ReportSection(
            title="Code Quality Issues",
            content=smells_content,
            subsections=smell_subsections
        )
        sections.append(smells_section)
    
    # Refactoring suggestions section
    if analysis.refactoring_suggestions:
        refactoring_content = f"Based on the analysis, {len(analysis.refactoring_suggestions)} refactoring suggestions have been identified:"
        
        refactoring_subsections = []
        for suggestion in analysis.refactoring_suggestions[:5]:  # Top 5 suggestions
            suggestion_section = ReportSection(
                title=suggestion.type,
                content=(
                    f"**Description**: {suggestion.description}\n\n"
                    f"**Files**: {', '.join(suggestion.file_paths)}\n\n"
                    f"**Rationale**: {suggestion.rationale}\n\n"
                    f"**Priority**: {suggestion.priority.capitalize()}\n\n"
                    f"**Before**:\n```\n{suggestion.before_snippet}\n```\n\n"
                    f"**After**:\n```\n{suggestion.after_snippet}\n```"
                )
            )
            refactoring_subsections.append(suggestion_section)
        
        if len(analysis.refactoring_suggestions) > 5:
            refactoring_content += f" Showing top 5 of {len(analysis.refactoring_suggestions)} suggestions."
            
        refactoring_section = ReportSection(
            title="Refactoring Suggestions",
            content=refactoring_content,
            subsections=refactoring_subsections
        )
        sections.append(refactoring_section)
    
    # Conclusion section
    conclusion_section = ReportSection(
        title="Conclusion",
        content=(
            f"This analysis has identified both strengths and areas for improvement in the codebase. "
            f"Overall quality score: {await calculate_quality_score(analysis)}/100. "
            f"By addressing the identified issues and implementing the suggested refactorings, "
            f"the codebase can become more maintainable, robust, and aligned with best practices."
        )
    )
    sections.append(conclusion_section)
    
    return sections
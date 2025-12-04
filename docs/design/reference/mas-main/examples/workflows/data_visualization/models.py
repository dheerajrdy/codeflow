"""
Data models for data visualization workflow.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VisualizationConfig(BaseModel):
    """Configuration for the data visualization workflow."""

    data_file: str
    output_dir: str = "./viz_output"
    azure_deployment: str = "gpt-4o-mini"
    max_goals: int = 5
    grammar_preference: str = "matplotlib"  # matplotlib, seaborn, plotly
    execution_timeout: int = 30
    force_refresh: bool = False


class DataSummaryResult(BaseModel):
    """Result from data loading and summarization."""

    rows: int
    columns: int
    column_types: Dict[str, str]
    summary_text: str
    sample_data: Dict[str, List[Any]]
    from_cache: bool


class VisualizationGoal(BaseModel):
    """Structured output for goal generation."""

    index: int
    question: str = Field(description="Clear analytical question about the data")
    chart_type: str = Field(
        description="Choose one: bar, line, scatter, histogram, boxplot, heatmap"
    )
    columns_needed: List[str] = Field(description="Exact column names from dataset")
    rationale: str = Field(description="Why this visualization provides insights")


class GoalGenerationResult(BaseModel):
    """Result from goal generation step."""

    goals_generated: int
    goals: List[VisualizationGoal]
    from_cache: bool


class GeneratedCode(BaseModel):
    """Structured output for code generation."""

    goal_index: int
    grammar: str = Field(description="matplotlib, seaborn, or plotly")
    imports: List[str] = Field(description="Required import statements")
    code_body: str = Field(description="Main visualization code")
    is_safe: bool = Field(description="True if code passes safety validation")
    safety_issues: List[str] = Field(description="List of potential security concerns")


class CodeGenerationResult(BaseModel):
    """Result from code generation step."""

    codes_generated: int
    safe_codes: int
    generated_codes: List[GeneratedCode]


class ExecutionResult(BaseModel):
    """Result from code execution step."""

    executions_attempted: int
    successful_executions: int
    output_files: List[str]
    execution_errors: List[str]

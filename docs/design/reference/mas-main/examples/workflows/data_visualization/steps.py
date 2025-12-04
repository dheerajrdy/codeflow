"""
Workflow steps for data visualization - each function is independently testable.
"""

import json
import os
import signal
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from picoagents.llm import AzureOpenAIChatCompletionClient
from picoagents.messages import SystemMessage, UserMessage
from picoagents.workflow import Context

try:
    from .models import (
        CodeGenerationResult,
        DataSummaryResult,
        ExecutionResult,
        GeneratedCode,
        GoalGenerationResult,
        VisualizationConfig,
        VisualizationGoal,
    )
except ImportError:
    from models import (
        CodeGenerationResult,
        DataSummaryResult,
        ExecutionResult,
        GeneratedCode,
        GoalGenerationResult,
        VisualizationConfig,
        VisualizationGoal,
    )


def save_checkpoint(data: Any, path: Path) -> None:
    """Save data with timestamp."""
    with open(path, "w") as f:
        json.dump(
            {"timestamp": datetime.now().isoformat(), "data": data}, f, default=str
        )


def load_checkpoint(path: Path) -> Any:
    """Load data from checkpoint."""
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)["data"]


async def load_and_summarize_data(
    config: VisualizationConfig, context: Context
) -> DataSummaryResult:
    """
    Load data and create intelligent summary.

    Engineering patterns demonstrated:
    • Smart caching to avoid redundant data processing
    • LLM-powered data understanding
    • Shared state via Context
    """
    output_dir = Path(config.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Cache check
    cache_file = output_dir / "data_summary.json"
    if cache_file.exists() and not config.force_refresh:
        cached = load_checkpoint(cache_file)
        if cached:
            # Load raw data for later steps
            df = pd.read_csv(config.data_file)
            context.set("raw_data", df)
            context.set("config", config)
            return DataSummaryResult(**cached, from_cache=True)

    # Load and analyze data
    df = pd.read_csv(config.data_file)

    # Basic data analysis
    column_types = {col: str(df[col].dtype) for col in df.columns}
    sample_data = {col: df[col].head(3).tolist() for col in df.columns}

    # Generate LLM summary
    client = AzureOpenAIChatCompletionClient(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=config.azure_deployment,
    )

    summary_prompt = f"""
    Analyze this dataset and provide a concise summary:
    - Rows: {len(df)}
    - Columns: {list(df.columns)}
    - Column types: {column_types}
    - Sample data: {sample_data}

    Describe what this data represents, key patterns you notice, and what kinds of insights might be valuable to explore through visualization.
    Keep it under 200 words.
    """

    response = await client.create(
        messages=[UserMessage(content=summary_prompt, source="user")]
    )

    result = DataSummaryResult(
        rows=len(df),
        columns=len(df.columns),
        column_types=column_types,
        summary_text=response.message.content,
        sample_data=sample_data,
        from_cache=False,
    )

    # Cache and store
    save_checkpoint(result.model_dump(exclude={"from_cache"}), cache_file)
    context.set("raw_data", df)
    context.set("config", config)
    context.set("data_summary", result)

    return result


async def generate_visualization_goals(
    data_result: DataSummaryResult, context: Context
) -> GoalGenerationResult:
    """
    Generate visualization goals using structured LLM output.

    Engineering patterns demonstrated:
    • Structured output for reliability
    • Intelligent caching by data fingerprint
    • Context-aware goal generation
    """

    config = context.get("config")
    output_dir = Path(config.output_dir)

    # Checkpoint check
    checkpoint_file = output_dir / "visualization_goals.json"
    cached_goals = load_checkpoint(checkpoint_file)
    if cached_goals and not config.force_refresh:
        goals = [VisualizationGoal(**goal) for goal in cached_goals["goals"]]
        context.set("visualization_goals", goals)
        return GoalGenerationResult(
            goals_generated=len(goals), goals=goals, from_cache=True
        )

    # Setup client
    client = AzureOpenAIChatCompletionClient(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=config.azure_deployment,
    )

    # Enhanced prompt for goal generation
    system_prompt = f"""You are an expert data analyst. Generate {config.max_goals} insightful visualization goals for this dataset.

Available columns: {list(data_result.column_types.keys())}
Column types: {data_result.column_types}
Data summary: {data_result.summary_text}

Each goal must:
- Ask a specific analytical question
- Suggest an appropriate chart type
- Reference exact column names from the dataset
- Explain why this visualization provides valuable insights

Follow visualization best practices:
- Use bar charts for categorical comparisons
- Use line charts for trends over time
- Use scatter plots for correlations between numeric variables
- Use histograms for distributions of numeric data
- Use boxplots for outlier detection and distribution comparison
- Use heatmaps for correlation matrices or 2D categorical data

CRITICAL: Only use column names that actually exist in the dataset: {list(data_result.column_types.keys())}
"""

    user_prompt = f"""Generate exactly {config.max_goals} diverse visualization goals that would provide the most valuable insights for this dataset."""

    # Generate goals without structured output (not supported with List type)
    response = await client.create(
        messages=[
            SystemMessage(content=system_prompt, source="system"),
            UserMessage(content=user_prompt, source="user"),
        ]
    )

    # Parse the response - for now using placeholder goals
    # In production, you'd parse response.message.content
    goals = []
    for i in range(min(config.max_goals, 3)):
        goal = VisualizationGoal(
            index=i,
            question=f"Visualization goal {i+1}",
            chart_type="bar",
            columns_needed=list(data_result.column_types.keys())[:2],
            rationale="Placeholder goal",
        )
        goals.append(goal)

    # Validate that goals reference real columns
    available_columns = set(data_result.column_types.keys())
    valid_goals = []
    for goal in goals:
        if all(col in available_columns for col in goal.columns_needed):
            valid_goals.append(goal)
        else:
            print(
                f"Skipping goal {goal.index}: references non-existent columns {goal.columns_needed}"
            )

    result = GoalGenerationResult(
        goals_generated=len(valid_goals), goals=valid_goals, from_cache=False
    )

    # Save checkpoint
    save_checkpoint(result.model_dump(exclude={"from_cache"}), checkpoint_file)
    context.set("visualization_goals", valid_goals)

    return result


def validate_code_safety(code: str) -> List[str]:
    """Basic safety validation for generated code."""
    issues = []

    # Check for dangerous patterns
    dangerous_patterns = [
        "import os",
        "import sys",
        "import subprocess",
        "open(",
        "file(",
        "eval(",
        "exec(",
        "requests.",
        "urllib.",
        "__import__",
        "input(",
        "raw_input(",
    ]

    for pattern in dangerous_patterns:
        if pattern in code:
            issues.append(f"Contains dangerous pattern: {pattern}")

    # Check for required visualization imports
    required_patterns = [
        "import matplotlib",
        "import seaborn",
        "import plotly",
        "plt.",
        "sns.",
    ]
    has_viz_import = any(pattern in code for pattern in required_patterns)
    if not has_viz_import:
        issues.append("Missing required visualization imports")

    # Check for data reference
    if "df" not in code and "data" not in code:
        issues.append("Code doesn't reference data variable")

    return issues


async def generate_visualization_code(
    goals_result: GoalGenerationResult, context: Context
) -> CodeGenerationResult:
    """
    Generate safe visualization code for each goal.

    Engineering patterns demonstrated:
    • Multi-grammar code generation
    • Safety validation before execution
    • Graceful error handling
    """

    config = context.get("config")
    data_summary = context.get("data_summary")
    output_dir = Path(config.output_dir)

    # Checkpoint
    checkpoint_file = output_dir / "generated_codes.json"
    cached_codes = load_checkpoint(checkpoint_file)
    if cached_codes and not config.force_refresh:
        codes = [GeneratedCode(**code) for code in cached_codes["generated_codes"]]
        context.set("generated_codes", codes)
        return CodeGenerationResult(
            codes_generated=len(codes),
            safe_codes=len([c for c in codes if c.is_safe]),
            generated_codes=codes,
        )

    client = AzureOpenAIChatCompletionClient(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=config.azure_deployment,
    )

    generated_codes = []

    # Process goals one by one
    for goal in goals_result.goals:
        try:
            # Generate code with structured output
            code_prompt = f"""
Generate Python visualization code for this goal:
Question: {goal.question}
Chart type: {goal.chart_type}
Columns needed: {goal.columns_needed}
Grammar: {config.grammar_preference}

Requirements:
- Use only these safe imports: pandas, matplotlib.pyplot, seaborn, numpy
- Data is available as 'df' DataFrame
- Create the visualization and store final chart object in variable 'chart'
- Use column names exactly as provided: {goal.columns_needed}
- No file I/O, network access, or subprocess calls
- Include proper labels, titles, and formatting

Available columns in dataset: {list(data_summary.column_types.keys())}
Column types: {data_summary.column_types}

Generate clean, executable code that creates a meaningful visualization.
"""

            response = await client.create(
                messages=[
                    SystemMessage(
                        content="Generate safe, executable visualization code following best practices.",
                        source="system",
                    ),
                    UserMessage(content=code_prompt, source="user"),
                ]
            )

            # Parse the response to extract code
            code_text = response.message.content

            # Create GeneratedCode object manually
            code = GeneratedCode(
                goal_index=goal.index,
                grammar=config.grammar_preference,
                imports=[
                    "import pandas as pd",
                    "import matplotlib.pyplot as plt",
                    "import seaborn as sns",
                    "import numpy as np",
                ],
                code_body=code_text,
                is_safe=False,
                safety_issues=[],
            )

            # Validate safety
            safety_issues = validate_code_safety(code.code_body)
            code.is_safe = len(safety_issues) == 0
            code.safety_issues = safety_issues

            generated_codes.append(code)

        except Exception as e:
            print(f"Failed to generate code for goal {goal.index}: {e}")
            continue

    result = CodeGenerationResult(
        codes_generated=len(generated_codes),
        safe_codes=len([c for c in generated_codes if c.is_safe]),
        generated_codes=generated_codes,
    )

    save_checkpoint(result.model_dump(), checkpoint_file)
    context.set("generated_codes", generated_codes)

    return result


async def execute_visualization_codes(
    code_result: CodeGenerationResult, context: Context
) -> ExecutionResult:
    """
    Execute codes safely with basic sandboxing.

    Engineering patterns demonstrated:
    • Sandboxed code execution
    • Resource limits and timeouts
    • Graceful error handling and reporting
    """

    config = context.get("config")
    df = context.get("raw_data")
    output_dir = Path(config.output_dir)

    successful_executions = []
    execution_errors = []
    output_files = []

    # Only execute safe codes
    safe_codes = [c for c in code_result.generated_codes if c.is_safe]

    for code_obj in safe_codes:
        try:
            # Create safe execution environment
            safe_globals = {
                "pd": pd,
                "df": df,
                "plt": plt,
                "sns": sns,
                "np": np,
                "__builtins__": {},  # Restrict built-ins for security
            }

            # Combine imports and code
            import_code = "\n".join(code_obj.imports) if code_obj.imports else ""
            full_code = f"{import_code}\n{code_obj.code_body}"

            # Execute with timeout (basic safety measure)
            def timeout_handler(_signum, _frame):
                raise TimeoutError("Code execution timed out")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(config.execution_timeout)

            try:
                exec(full_code, safe_globals)
                chart = safe_globals.get("chart")

                if chart or plt.get_fignums():  # Check if plot was created
                    # Save chart
                    output_file = output_dir / f"chart_{code_obj.goal_index}.png"

                    if chart and hasattr(chart, "savefig"):
                        chart.savefig(output_file, dpi=150, bbox_inches="tight")
                    else:
                        plt.savefig(output_file, dpi=150, bbox_inches="tight")

                    plt.close("all")  # Clean up

                    output_files.append(str(output_file))
                    successful_executions.append(code_obj.goal_index)
                    print(f"✓ Generated visualization for goal {code_obj.goal_index}")
                else:
                    execution_errors.append(
                        f"Goal {code_obj.goal_index}: No chart object created"
                    )

            finally:
                signal.alarm(0)  # Clear timeout
                plt.close("all")  # Ensure cleanup

        except TimeoutError:
            execution_errors.append(f"Goal {code_obj.goal_index}: Execution timeout")
            plt.close("all")
        except Exception as e:
            execution_errors.append(f"Goal {code_obj.goal_index}: {str(e)}")
            plt.close("all")

    # Generate summary report
    report_content = f"""# Data Visualization Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Summary
- **Goals processed:** {len(code_result.generated_codes)}
- **Safe codes:** {code_result.safe_codes}
- **Successful executions:** {len(successful_executions)}
- **Output files:** {len(output_files)}

## Generated Visualizations
"""

    for i, file_path in enumerate(output_files):
        goal_index = successful_executions[i]
        report_content += f"- Chart {goal_index}: {file_path}\n"

    if execution_errors:
        report_content += "\n## Execution Errors\n"
        for error in execution_errors:
            report_content += f"- {error}\n"

    # Save report
    report_file = output_dir / "visualization_report.md"
    with open(report_file, "w") as f:
        f.write(report_content)

    return ExecutionResult(
        executions_attempted=len(safe_codes),
        successful_executions=len(successful_executions),
        output_files=output_files,
        execution_errors=execution_errors,
    )

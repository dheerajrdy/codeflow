"""
Data Visualization Workflow - Main orchestration

Demonstrates advanced workflow patterns:
• Intelligent data summarization with LLM insights
• Structured goal generation for diverse visualizations
• Safe code generation with validation
• Sandboxed execution with resource limits

Usage: python workflow.py
Requires: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY environment variables
"""

import asyncio
import os
import time
from pathlib import Path

from picoagents.workflow import (
    FunctionStep,
    StepMetadata,
    Workflow,
    WorkflowMetadata,
    WorkflowRunner,
)

try:
    from .models import (
        CodeGenerationResult,
        DataSummaryResult,
        ExecutionResult,
        GoalGenerationResult,
        VisualizationConfig,
    )
    from .steps import (
        execute_visualization_codes,
        generate_visualization_code,
        generate_visualization_goals,
        load_and_summarize_data,
    )
except ImportError:
    from models import (
        CodeGenerationResult,
        DataSummaryResult,
        ExecutionResult,
        GoalGenerationResult,
        VisualizationConfig,
    )
    from steps import (
        execute_visualization_codes,
        generate_visualization_code,
        generate_visualization_goals,
        load_and_summarize_data,
    )


async def create_visualization_workflow(config: VisualizationConfig) -> Workflow:
    """Create the data visualization workflow with chained steps."""

    steps = [
        FunctionStep(
            "summarize",
            StepMetadata(
                name="Data Summary",
                description="Load and intelligently summarize dataset",
            ),
            VisualizationConfig,
            DataSummaryResult,
            load_and_summarize_data,
        ),
        FunctionStep(
            "goals",
            StepMetadata(
                name="Goal Generation",
                description="Generate diverse visualization objectives",
            ),
            DataSummaryResult,
            GoalGenerationResult,
            generate_visualization_goals,
        ),
        FunctionStep(
            "generate",
            StepMetadata(
                name="Code Generation", description="Generate safe visualization code"
            ),
            GoalGenerationResult,
            CodeGenerationResult,
            generate_visualization_code,
        ),
        FunctionStep(
            "execute",
            StepMetadata(
                name="Safe Execution", description="Execute code with sandboxing"
            ),
            CodeGenerationResult,
            ExecutionResult,
            execute_visualization_codes,
        ),
    ]

    workflow = Workflow(
        metadata=WorkflowMetadata(
            name="Data Visualization Pipeline",
            description="Automated data visualization generation using LLMs and workflow patterns",
        ),
        initial_state={"config": config},
    ).chain(*steps)

    return workflow


async def main():
    """Run the data visualization workflow."""

    # Check environment
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        print(
            "❌ Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables"
        )
        return

    print("📊 Data Visualization Workflow")
    print("=" * 40)

    # Configure workflow
    config = VisualizationConfig(
        data_file="./sample_data.csv",  # Replace with your data file
        output_dir="./viz_output",
        azure_deployment="gpt-4o-mini",
        max_goals=5,
        grammar_preference="matplotlib",
        execution_timeout=30,
        force_refresh=False,
    )

    # Ensure output directory exists
    Path(config.output_dir).mkdir(exist_ok=True)

    # Check if data file exists
    if not Path(config.data_file).exists():
        print(f"❌ Data file not found: {config.data_file}")
        print("Please provide a CSV file to visualize.")
        return

    print(f"📁 Data file: {config.data_file}")
    print(f"📂 Output directory: {config.output_dir}")
    print(f"🎯 Max goals: {config.max_goals}")
    print(f"📊 Grammar: {config.grammar_preference}")

    # Run workflow
    workflow = await create_visualization_workflow(config)
    runner = WorkflowRunner()

    start_time = time.time()

    try:
        async for event in runner.run_stream(workflow, config.model_dump()):
            pass  # Process events

        execution_time = time.time() - start_time

        print(f"\n✅ Workflow completed in {execution_time:.1f}s")
        print(f"📄 Check results in: {config.output_dir}/")

        # List generated files
        output_dir = Path(config.output_dir)
        png_files = list(output_dir.glob("*.png"))
        if png_files:
            print(f"🖼️  Generated {len(png_files)} visualizations:")
            for file in png_files:
                print(f"   - {file.name}")

        report_file = output_dir / "visualization_report.md"
        if report_file.exists():
            print(f"📊 Summary report: {report_file}")

    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

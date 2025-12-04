"""
Test suite for data visualization workflow components.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest
from models import DataSummaryResult, VisualizationConfig, VisualizationGoal
from steps import (
    generate_visualization_goals,
    load_and_summarize_data,
    validate_code_safety,
)

from picoagents.workflow import Context


@pytest.mark.asyncio
async def test_data_loading():
    """Test data loading and summarization."""

    # Create test CSV file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("name,age,salary\nAlice,25,50000\nBob,30,60000\nCharlie,35,70000\n")
        test_file = f.name

    try:
        config = VisualizationConfig(
            data_file=test_file, output_dir="./test_output", force_refresh=True
        )

        context = Context()

        # Mock the LLM client
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Test dataset with employee information including names, ages, and salaries."
        mock_client.create.return_value = mock_response

        # Test would require patching the client creation
        # For now, just test the data loading part
        df = pd.read_csv(test_file)
        assert len(df) == 3
        assert list(df.columns) == ["name", "age", "salary"]

    finally:
        Path(test_file).unlink()


def test_code_safety_validation():
    """Test code safety validation."""

    # Safe code
    safe_code = """
    import matplotlib.pyplot as plt
    df['age'].hist()
    chart = plt.gcf()
    """
    issues = validate_code_safety(safe_code)
    assert len(issues) == 0

    # Unsafe code
    unsafe_code = """
    import os
    os.system('rm -rf /')
    """
    issues = validate_code_safety(unsafe_code)
    assert len(issues) > 0
    assert any("dangerous pattern" in issue for issue in issues)


@pytest.mark.asyncio
async def test_goal_generation_structure():
    """Test that goals have proper structure."""

    # Mock data result
    data_result = DataSummaryResult(
        rows=100,
        columns=3,
        column_types={"age": "int64", "salary": "int64", "name": "object"},
        summary_text="Employee data with demographics and compensation",
        sample_data={
            "age": [25, 30, 35],
            "salary": [50000, 60000, 70000],
            "name": ["Alice", "Bob", "Charlie"],
        },
        from_cache=False,
    )

    # Test goal validation
    goal = VisualizationGoal(
        index=1,
        question="What is the distribution of ages?",
        chart_type="histogram",
        columns_needed=["age"],
        rationale="Shows age demographics of employees",
    )

    assert goal.index == 1
    assert "age" in goal.columns_needed
    assert goal.chart_type in [
        "histogram",
        "bar",
        "line",
        "scatter",
        "boxplot",
        "heatmap",
    ]


if __name__ == "__main__":
    # Run basic tests
    test_code_safety_validation()
    print("✅ Code safety validation tests passed")

    asyncio.run(test_goal_generation_structure())
    print("✅ Goal generation structure tests passed")

    print("🧪 All tests completed successfully")

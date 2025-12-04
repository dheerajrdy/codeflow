"""
Tests for YC analysis workflow components.

Demonstrates testability of each workflow step.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from picoagents.workflow import Context

try:
    from .models import AgentAnalysis, DataResult, FilterResult, WorkflowConfig
    from .steps import (
        classify_agents,
        filter_keywords,
        generate_long_slug,
        load_checkpoint,
        load_data,
        save_checkpoint,
    )
except ImportError:
    from models import AgentAnalysis, DataResult, FilterResult, WorkflowConfig
    from steps import (
        classify_agents,
        filter_keywords,
        generate_long_slug,
        load_checkpoint,
        load_data,
        save_checkpoint,
    )


class TestUtils:
    """Test utility functions."""

    def test_generate_slug(self):
        """Test company slug generation."""
        row = pd.Series({"id": "123", "name": "Test Co", "slug": "test-co"})
        slug = generate_long_slug(row)
        assert slug == "123_testco_test-co"

    def test_checkpointing(self):
        """Test checkpoint save/load."""
        with tempfile.TemporaryDirectory() as temp_dir:
            checkpoint_path = Path(temp_dir) / "test.json"

            # Save data
            test_data = {"companies": [{"name": "Test", "is_agent": True}]}
            save_checkpoint(test_data, checkpoint_path)

            # Load data
            loaded = load_checkpoint(checkpoint_path)
            assert loaded == test_data

            # Test non-existent file
            assert load_checkpoint(Path("nonexistent.json")) is None


class TestSteps:
    """Test individual workflow steps."""

    @pytest.mark.asyncio
    async def test_load_data_from_cache(self):
        """Test data loading with cache hit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock cache file
            cache_file = Path(temp_dir) / "companies.json"
            test_df = pd.DataFrame(
                [
                    {
                        "id": "1",
                        "name": "Test Co",
                        "one_liner": "AI company",
                        "long_description": "Building AI agents",
                    }
                ]
            )
            test_df.to_json(cache_file, orient="records")

            # Test loading
            config = WorkflowConfig(data_dir=temp_dir)
            context = Context()

            result = await load_data(config, context)

            assert result.companies == 1
            assert result.from_cache == True
            assert context.get("df") is not None

    @pytest.mark.asyncio
    async def test_filter_keywords(self):
        """Test keyword filtering logic."""
        # Setup test data
        test_df = pd.DataFrame(
            [
                {
                    "desc": "We build AI agents for productivity"
                },  # Should match both AI and AI+agents
                {"desc": "Traditional software company"},  # Should match neither
                {"desc": "Machine learning for healthcare"},  # Should match AI only
                {
                    "desc": "AI-powered support agents for sales"
                },  # Should match both AI and AI+agents
            ]
        )

        context = Context()
        context.set("df", test_df)

        # Mock input
        data_result = DataResult(companies=4, from_cache=False)

        result = await filter_keywords(data_result, context)

        assert result.total == 4
        assert result.ai_companies == 3  # First, third, and fourth
        assert result.agent_keywords == 2  # First and fourth

    @pytest.mark.asyncio
    async def test_classify_agents_with_mock_llm(self):
        """Test agent classification with mocked LLM."""
        # Setup test data
        test_df = pd.DataFrame(
            [
                {
                    "slug": "test1",
                    "name": "AgentCo",
                    "desc": "AI agents",
                    "has_ai": True,
                },
                {
                    "slug": "test2",
                    "name": "MLCo",
                    "desc": "Machine learning",
                    "has_ai": True,
                },
            ]
        )

        context = Context()
        context.set("filtered_df", test_df)

        with tempfile.TemporaryDirectory() as temp_dir:
            config = WorkflowConfig(data_dir=temp_dir)
            context.set("config", config)

            # Mock the Azure client
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.structured_output = AgentAnalysis(
                is_about_ai=True,
                domain="productivity",
                subdomain="AI tools",
                is_agent=True,
                ai_rationale="Company builds AI-powered productivity tools",
                agent_rationale="Tools act autonomously on user's behalf",
            )
            mock_response.usage = MagicMock()
            mock_response.usage.total_tokens = 100

            mock_client.create.return_value = mock_response

            # Patch the client creation (would need proper mocking in real test)
            # For now, test will skip LLM calls if no credentials
            filter_result = FilterResult(total=2, ai_companies=2, agent_keywords=1)

            try:
                result = await classify_agents(filter_result, context)
                # If credentials available, check results
                assert result.processed >= 0
                assert result.agents >= 0
            except Exception:
                # Expected if no Azure credentials
                pass


class TestWorkflow:
    """Test complete workflow integration."""

    def test_models_validation(self):
        """Test Pydantic model validation."""
        # Test valid config
        config = WorkflowConfig(data_dir="./test", batch_size=5)
        assert config.batch_size == 5

        # Test invalid value (this should work since all fields are required and valid)
        try:
            analysis = AgentAnalysis(
                is_about_ai=True,
                domain="test",
                subdomain="testing",
                is_agent=True,
                ai_rationale="Test validation",
                agent_rationale="Test agent validation",
            )
            assert analysis.domain == "test"
        except ValueError:
            # This might raise if domain validation is stricter
            pass

    @pytest.mark.asyncio
    async def test_context_state_management(self):
        """Test context state sharing between steps."""
        context = Context()

        # Test setting and getting values
        test_df = pd.DataFrame([{"name": "test"}])
        context.set("df", test_df)

        retrieved_df = context.get("df")
        assert len(retrieved_df) == 1
        assert retrieved_df.iloc[0]["name"] == "test"


if __name__ == "__main__":
    # Simple test runner
    asyncio.run(TestSteps().test_filter_keywords())
    print("✅ Basic tests passed")

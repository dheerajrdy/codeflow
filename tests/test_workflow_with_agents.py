"""Tests for workflow with real agents."""

import pytest
from src.orchestration import WorkflowEngine
from src.agents.design_agent import DesignAgent
from src.agents.review_agent import ReviewAgent
from src.models import ModelClient, Message, ModelResponse


class MockModelClient(ModelClient):
    """Mock model client for testing."""

    def __init__(self):
        self.call_count = 0

    async def chat(self, messages, temperature=None, max_tokens=None):
        self.call_count += 1

        # Check if this is a Design Agent call or Review Agent call
        system_msg = messages[0].content if messages else ""

        if "design" in system_msg.lower():
            # Design Agent response
            return ModelResponse(
                content="""
PROBLEM UNDERSTANDING:
Need to implement the feature described in the ticket.

PROPOSED APPROACH:
Create a new module with the required functionality and add comprehensive tests.

TARGET FILES:
src/new_feature.py
tests/test_new_feature.py

STEP-BY-STEP PLAN:
1. Create the new_feature module
2. Implement core functionality
3. Add unit tests
4. Update documentation
""",
                model="mock-model",
            )
        else:
            # Review Agent response
            return ModelResponse(
                content="""
DECISION: APPROVED

REVIEW COMMENTS:
- Implementation meets acceptance criteria
- Tests are passing
- Code quality is good

SUGGESTIONS:
- Consider adding more edge case tests
""",
                model="mock-model",
            )

    def get_model_name(self) -> str:
        return "mock-model"


class TestWorkflowWithAgents:
    """Tests for workflow engine with real agents."""

    @pytest.mark.asyncio
    async def test_workflow_with_mock_agents(self):
        """Test workflow with Design and Review agents using mock model."""
        mock_client = MockModelClient()

        design_agent = DesignAgent(mock_client)
        review_agent = ReviewAgent(mock_client)

        engine = WorkflowEngine(
            design_agent=design_agent,
            review_agent=review_agent,
        )

        context = await engine.run(
            ticket_id="TEST-AGENTS-001",
            dry_run=True,
        )

        # Verify workflow completed successfully
        assert context.is_successful()
        assert len(context.completed_steps) == 8

        # Verify Design Agent was called
        assert context.design is not None
        assert "feature" in context.design.problem_understanding.lower()
        assert len(context.design.target_files) == 2
        assert "src/new_feature.py" in context.design.target_files

        # Verify Review Agent was called
        assert context.review is not None
        assert context.review.decision == "approved"
        assert len(context.review.comments) > 0

        # Verify model was called twice (once for design, once for review)
        assert mock_client.call_count == 2

    @pytest.mark.asyncio
    async def test_workflow_with_stub_agents(self):
        """Test that workflow still works without agents (stub mode)."""
        engine = WorkflowEngine()  # No agents provided

        context = await engine.run(
            ticket_id="TEST-STUB-001",
            dry_run=True,
        )

        # Should still complete successfully with stubs
        assert context.is_successful()
        assert len(context.completed_steps) == 8

        # Stub data should be present
        assert context.design is not None
        assert context.review is not None
        assert context.review.decision == "approved"


class TestWorkflowAgentIntegration:
    """Integration tests for workflow with agents."""

    @pytest.mark.asyncio
    async def test_design_agent_output_flows_to_review(self):
        """Test that Design Agent output is used by Review Agent."""
        mock_client = MockModelClient()
        design_agent = DesignAgent(mock_client)
        review_agent = ReviewAgent(mock_client)

        engine = WorkflowEngine(
            design_agent=design_agent,
            review_agent=review_agent,
        )

        context = await engine.run(
            ticket_id="TEST-FLOW-001",
            dry_run=True,
        )

        # Design output should influence review
        assert context.design is not None
        assert context.review is not None

        # The review agent receives the design output
        # (We can't directly verify this, but we can check the flow completed)
        assert context.is_successful()

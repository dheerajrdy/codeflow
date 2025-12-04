"""Tests for workflow engine and steps."""

import pytest
from src.orchestration import WorkflowEngine, WorkflowContext
from src.orchestration.context import TicketInfo, RepoInfo


class TestWorkflowEngine:
    """Tests for WorkflowEngine."""

    @pytest.mark.asyncio
    async def test_workflow_runs_successfully(self):
        """Test that the workflow runs all steps successfully."""
        engine = WorkflowEngine()
        context = await engine.run(
            ticket_id="TEST-001",
            dry_run=True,
        )

        # Check that all steps completed
        assert len(context.completed_steps) == 8
        assert "FetchTicket" in context.completed_steps
        assert "AnalyzeRepo" in context.completed_steps
        assert "Design" in context.completed_steps
        assert "Coding" in context.completed_steps
        assert "Test" in context.completed_steps
        assert "Review" in context.completed_steps
        assert "CreatePR" in context.completed_steps
        assert "Notes" in context.completed_steps

        # Check successful completion
        assert context.is_successful()
        assert len(context.errors) == 0

        # Check ticket was fetched
        assert context.ticket is not None
        assert context.ticket.ticket_id == "TEST-001"

        # Check repo info was populated
        assert context.repo is not None
        assert context.repo.main_language == "Python"

        # Check design output
        assert context.design is not None
        assert len(context.design.target_files) > 0

        # Check coding output
        assert context.coding is not None
        assert len(context.coding.files_changed) > 0

        # Check test results
        assert context.test is not None
        assert context.test.success is True

        # Check review decision
        assert context.review is not None
        assert context.review.decision == "approved"

        # Check PR was created
        assert context.pr is not None
        assert "TEST-001" in context.pr.branch_name

        # Check notes were generated
        assert context.notes is not None
        assert len(context.notes.summary) > 0

    @pytest.mark.asyncio
    async def test_dry_run_mode(self):
        """Test that dry-run mode is respected."""
        engine = WorkflowEngine()
        context = await engine.run(
            ticket_id="TEST-002",
            dry_run=True,
        )

        assert context.dry_run is True
        assert context.is_successful()


class TestWorkflowContext:
    """Tests for WorkflowContext."""

    def test_context_initialization(self):
        """Test that WorkflowContext initializes correctly."""
        context = WorkflowContext(run_id="test-123")

        assert context.run_id == "test-123"
        assert context.ticket is None
        assert context.repo is None
        assert len(context.completed_steps) == 0
        assert len(context.errors) == 0
        assert context.dry_run is False

    def test_mark_step_complete(self):
        """Test marking steps as complete."""
        context = WorkflowContext(run_id="test-123")

        context.mark_step_complete("Step1")
        assert "Step1" in context.completed_steps

        context.mark_step_complete("Step2")
        assert len(context.completed_steps) == 2

        # Should not duplicate
        context.mark_step_complete("Step1")
        assert len(context.completed_steps) == 2

    def test_add_error(self):
        """Test adding errors to context."""
        context = WorkflowContext(run_id="test-123")
        context.current_step = "TestStep"

        context.add_error("Something went wrong")
        assert len(context.errors) == 1
        assert "TestStep" in context.errors[0]
        assert "Something went wrong" in context.errors[0]

    def test_is_successful(self):
        """Test success detection."""
        context = WorkflowContext(run_id="test-123")

        # Not completed yet
        assert not context.is_successful()

        # Complete but with errors
        from datetime import datetime
        context.completed_at = datetime.now()
        context.add_error("Error")
        assert not context.is_successful()

        # Complete without errors
        context2 = WorkflowContext(run_id="test-456")
        context2.completed_at = datetime.now()
        assert context2.is_successful()

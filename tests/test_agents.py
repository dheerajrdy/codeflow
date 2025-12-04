"""Tests for agents."""

import pytest
from src.models import ModelClient, Message, ModelResponse
from src.agents.design_agent import DesignAgent
from src.agents.coding_agent import CodingAgent
from src.agents.review_agent import ReviewAgent
from src.agents.notes_agent import NotesAgent
from src.orchestration.context import (
    TicketInfo,
    RepoInfo,
    DesignOutput,
    TestOutput,
)


class MockModelClient(ModelClient):
    """Mock model client for testing."""

    def __init__(self, response_text: str):
        self.response_text = response_text
        self.last_messages = None

    async def chat(self, messages, temperature=None, max_tokens=None):
        self.last_messages = messages
        return ModelResponse(
            content=self.response_text,
            model="mock-model",
        )

    def get_model_name(self) -> str:
        return "mock-model"


class TestDesignAgent:
    """Tests for Design Agent."""

    @pytest.mark.asyncio
    async def test_design_agent_parses_response(self):
        """Test that Design Agent correctly parses model response."""
        response_text = """
PROBLEM UNDERSTANDING:
We need to implement a login feature for the application.

PROPOSED APPROACH:
Create a login component with username/password fields and validate against the backend API.

TARGET FILES:
src/components/Login.tsx
src/api/auth.ts
tests/components/Login.test.tsx

STEP-BY-STEP PLAN:
1. Create Login component with form fields
2. Implement API call to /auth/login endpoint
3. Add error handling for invalid credentials
4. Write unit tests for the component
"""

        mock_client = MockModelClient(response_text)
        agent = DesignAgent(mock_client)

        ticket = TicketInfo(
            ticket_id="TEST-123",
            title="Add login feature",
            description="Users should be able to log in",
            acceptance_criteria="Login form works",
        )

        repo = RepoInfo(
            repo_path="/test/repo",
            main_language="TypeScript",
            test_command="npm test",
        )

        result = await agent.run(ticket, repo)

        assert isinstance(result, DesignOutput)
        assert "login feature" in result.problem_understanding.lower()
        assert "component" in result.proposed_approach.lower()
        assert len(result.target_files) == 3
        assert "src/components/Login.tsx" in result.target_files
        assert len(result.step_by_step_plan) == 4
        assert "Login component" in result.step_by_step_plan[0]


class TestReviewAgent:
    """Tests for Review Agent."""

    @pytest.mark.asyncio
    async def test_review_agent_approves(self):
        """Test that Review Agent can approve changes."""
        response_text = """
DECISION: APPROVED

REVIEW COMMENTS:
- Code changes meet the acceptance criteria
- Tests are passing successfully
- Implementation follows best practices

SUGGESTIONS:
- Consider adding integration tests
- Add JSDoc comments to exported functions
"""

        mock_client = MockModelClient(response_text)
        agent = ReviewAgent(mock_client)

        ticket = TicketInfo(
            ticket_id="TEST-123",
            title="Add feature",
            acceptance_criteria="Feature works",
        )

        design = DesignOutput(
            problem_understanding="Need feature",
            proposed_approach="Implement it",
        )

        test_output = TestOutput(
            success=True,
            output="All tests passed",
        )

        result = await agent.run(
            ticket,
            design,
            diff="+ new code",
            test_output=test_output,
        )

        assert result.decision == "approved"
        assert len(result.comments) == 3
        assert any("acceptance criteria" in c.lower() for c in result.comments)
        assert len(result.suggestions) == 2

    @pytest.mark.asyncio
    async def test_review_agent_rejects(self):
        """Test that Review Agent can reject changes."""
        response_text = """
DECISION: REJECTED

REVIEW COMMENTS:
- Tests are failing
- Code does not meet acceptance criteria
- Missing error handling

SUGGESTIONS:
- Fix the failing tests
- Add proper error handling
"""

        mock_client = MockModelClient(response_text)
        agent = ReviewAgent(mock_client)

        ticket = TicketInfo(ticket_id="TEST-123")
        design = DesignOutput()
        test_output = TestOutput(success=False, errors="Tests failed")

        result = await agent.run(ticket, design, diff="", test_output=test_output)

        assert result.decision == "rejected"
        assert len(result.comments) == 3
        assert len(result.suggestions) == 2


class TestAgentIntegration:
    """Integration tests for agents."""

    @pytest.mark.asyncio
    async def test_design_agent_with_minimal_response(self):
        """Test Design Agent with minimal model response."""
        response_text = "PROBLEM UNDERSTANDING:\nNeed to add feature\n\nPROPOSED APPROACH:\nImplement it"

        mock_client = MockModelClient(response_text)
        agent = DesignAgent(mock_client)

        ticket = TicketInfo(ticket_id="TEST-123", title="Test")
        repo = RepoInfo()

        result = await agent.run(ticket, repo)

        # Should return valid DesignOutput even with minimal response
        assert isinstance(result, DesignOutput)
        assert result.problem_understanding
        assert result.proposed_approach

    @pytest.mark.asyncio
    async def test_review_agent_with_minimal_response(self):
        """Test Review Agent with minimal model response."""
        response_text = "DECISION: APPROVED"

        mock_client = MockModelClient(response_text)
        agent = ReviewAgent(mock_client)

        ticket = TicketInfo(ticket_id="TEST-123")
        design = DesignOutput()
        test_output = TestOutput(success=True)

        result = await agent.run(ticket, design, diff="", test_output=test_output)

        assert result.decision == "approved"


class TestCodingAgent:
    """Tests for Coding Agent."""

    @pytest.mark.asyncio
    async def test_coding_agent_parses_diff(self):
        """Coding Agent should parse diff, files, and explanations."""
        response_text = """
PATCH:
```diff
--- a/src/example.py
+++ b/src/example.py
@@
-print("old")
+print("new")
```

FILES CHANGED:
- src/example.py

EXPLANATIONS:
- Replaced log message
"""
        mock_client = MockModelClient(response_text)
        agent = CodingAgent(mock_client)

        ticket = TicketInfo(ticket_id="TEST-789", title="Update message")
        design = DesignOutput(
            problem_understanding="Change print output",
            proposed_approach="Update message string",
            target_files=["src/example.py"],
        )
        repo = RepoInfo(repo_path="/tmp/repo", main_language="Python", test_command="pytest")

        result = await agent.run(ticket, design, repo)

        assert isinstance(result.diff, str)
        assert "print(\"new\")" in result.diff or 'print("new")' in result.diff
        assert "src/example.py" in result.files_changed
        assert "Replaced log message" in result.explanations

    def test_build_code_context_truncates(self, tmp_path):
        """Ensure build_code_context truncates large files."""
        long_content = "a" * 6000
        file_path = tmp_path / "big.txt"
        file_path.write_text(long_content, encoding="utf-8")

        context = CodingAgent.build_code_context(tmp_path, ["big.txt"], max_bytes=100)

        assert "big.txt" in context
        assert len(context["big.txt"]) <= 110  # includes truncation note
        assert "... [truncated]" in context["big.txt"]


class TestNotesAgent:
    """Tests for Notes Agent."""

    @pytest.mark.asyncio
    async def test_notes_agent_parses_response(self):
        """Notes Agent should parse sections into NotesOutput."""
        response_text = """
SUMMARY:
- Completed workflow for TEST-1
- PR opened

LESSONS:
- Tests were fast

SUGGESTIONS:
- Add more edge cases

TAGS:
- success
- python
"""
        mock_client = MockModelClient(response_text)
        agent = NotesAgent(mock_client)

        result = await agent.run(
            ticket_summary="TEST-1: title",
            design_summary="Did a thing",
            coding_summary="Changed files",
            test_summary="PASS",
            review_summary="APPROVED",
            pr_summary="https://example.com/pr/1",
            logs="log1\nlog2",
        )

        assert "Completed workflow" in result.summary
        assert "Tests were fast" in result.lessons_learned[0]
        assert "edge cases" in result.suggestions[0]
        assert "success" in result.tags

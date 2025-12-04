"""WorkflowContext for sharing data between workflow steps."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime


@dataclass
class TicketInfo:
    """Jira ticket information."""
    ticket_id: str
    title: str = ""
    description: str = ""
    acceptance_criteria: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RepoInfo:
    """Repository metadata."""
    repo_path: str = ""
    main_language: str = ""
    test_command: str = ""
    repo_url: str = ""
    default_branch: str = "main"


@dataclass
class DesignOutput:
    """Output from Design Agent."""
    problem_understanding: str = ""
    proposed_approach: str = ""
    target_files: list[str] = field(default_factory=list)
    step_by_step_plan: list[str] = field(default_factory=list)


@dataclass
class CodingOutput:
    """Output from Coding Agent."""
    patches: list[str] = field(default_factory=list)
    diff: str = ""
    explanations: str = ""
    files_changed: list[str] = field(default_factory=list)


@dataclass
class TestOutput:
    """Test execution results."""
    success: bool = False
    output: str = ""
    errors: str = ""
    duration_seconds: float = 0.0


@dataclass
class ReviewOutput:
    """Output from Review Agent."""
    decision: str = "pending"  # "approved", "rejected", "pending"
    comments: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class PRInfo:
    """Pull request information."""
    branch_name: str = ""
    pr_url: str = ""
    pr_number: Optional[int] = None


@dataclass
class NotesOutput:
    """Output from Notes/Metadata Agent."""
    summary: str = ""
    lessons_learned: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class WorkflowContext:
    """
    Shared context object that flows through all workflow steps.
    Each step reads from and writes to this context.
    """

    # Run metadata
    run_id: str
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    # Step data
    ticket: Optional[TicketInfo] = None
    repo: Optional[RepoInfo] = None
    design: Optional[DesignOutput] = None
    coding: Optional[CodingOutput] = None
    test: Optional[TestOutput] = None
    review: Optional[ReviewOutput] = None
    pr: Optional[PRInfo] = None
    notes: Optional[NotesOutput] = None

    # Execution tracking
    current_step: str = ""
    completed_steps: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)

    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False

    def mark_step_complete(self, step_name: str) -> None:
        """Mark a step as completed."""
        if step_name not in self.completed_steps:
            self.completed_steps.append(step_name)

    def add_error(self, error: str) -> None:
        """Add an error to the context."""
        self.errors.append(f"[{self.current_step}] {error}")

    def add_log(self, message: str) -> None:
        """Record a log message for observability."""
        self.logs.append(message)

    def is_successful(self) -> bool:
        """Check if the workflow completed successfully."""
        return len(self.errors) == 0 and self.completed_at is not None

"""Workflow engine for orchestrating multi-agent workflow steps."""

import uuid
from datetime import datetime
from typing import List, Optional

from .context import WorkflowContext
from .run_store import save_run
from .steps import (
    WorkflowStep,
    FetchTicketStep,
    AnalyzeRepoStep,
    DesignStep,
    CodingStep,
    TestStep,
    ReviewStep,
    CreatePRStep,
    NotesStep,
)


class WorkflowEngine:
    """
    Sequential workflow engine that runs steps in order.
    Each step receives the shared WorkflowContext and can update it.
    """

    def __init__(
        self,
        design_agent=None,
        coding_agent=None,
        review_agent=None,
        jira_client=None,
        github_client=None,
        notes_agent=None,
        auto_confirm: bool = False,
    ):
        """
        Initialize the workflow engine with steps.

        Args:
            design_agent: Optional Design Agent instance (uses stub if None)
            coding_agent: Optional Coding Agent instance (uses stub if None)
            review_agent: Optional Review Agent instance (uses stub if None)
            jira_client: Optional Jira client for fetching tickets
            github_client: Optional GitHub client for branch/PR operations
            notes_agent: Optional Notes Agent instance (uses stub if None)
            auto_confirm: Whether to skip interactive confirmations for git/PR actions
        """
        self.fetch_step = FetchTicketStep(jira_client=jira_client)
        self.analyze_step = AnalyzeRepoStep()
        self.design_step = DesignStep(design_agent=design_agent)
        self.coding_step = CodingStep(coding_agent=coding_agent)
        self.test_step = TestStep()
        self.review_step = ReviewStep(review_agent=review_agent)
        self.pr_step = CreatePRStep(github_client=github_client, auto_confirm=auto_confirm)
        self.notes_step = NotesStep(notes_agent=notes_agent)

        # Keep steps list for summary/consistency (Coding/Test/Review handled in a retry loop)
        self.steps: List[WorkflowStep] = [
            self.fetch_step,
            self.analyze_step,
            self.design_step,
            self.coding_step,
            self.test_step,
            self.review_step,
            self.pr_step,
            self.notes_step,
        ]

    async def run(
        self,
        ticket_id: str,
        config: Optional[dict] = None,
        dry_run: bool = False,
    ) -> WorkflowContext:
        """
        Run the complete workflow for a given ticket.

        Args:
            ticket_id: Jira ticket ID to process
            config: Optional configuration dictionary
            dry_run: If True, skip destructive operations

        Returns:
            WorkflowContext with all results
        """
        # Initialize context
        run_id = str(uuid.uuid4())[:8]
        context = WorkflowContext(
            run_id=run_id,
            config=config or {},
            dry_run=dry_run,
        )
        context.config["ticket_id"] = ticket_id

        print(f"\n{'='*60}")
        print(f"WORKFLOW RUN: {run_id}")
        print(f"TICKET: {ticket_id}")
        print(f"DRY RUN: {dry_run}")
        print(f"{'='*60}")

        # Run each step sequentially
        idx = 0
        while idx < len(self.steps):
            step = self.steps[idx]
            try:
                if step is self.coding_step:
                    context = await self._run_coding_test_review_with_retries(context)
                    # Skip Test/Review in the main loop (they were executed in the retry loop)
                    idx += 3  # advance past coding, test, review
                    continue
                if step in (self.test_step, self.review_step):
                    idx += 1
                    continue
                context = await step.run(context)
            except Exception as e:
                print(f"\n{'='*60}")
                print(f"WORKFLOW FAILED")
                print(f"{'='*60}")
                print(f"Error: {e}")
                break
            idx += 1

        # Mark completion
        context.completed_at = datetime.now()

        # Print summary
        self._print_summary(context)

        # Persist run for observability
        try:
            runs_dir = context.config.get("runs_dir", "runs")
            save_run(context, runs_dir=runs_dir)
        except Exception as exc:
            print(f"Warning: failed to save run metadata: {exc}")

        return context

    async def _run_coding_test_review_with_retries(self, context: WorkflowContext) -> WorkflowContext:
        """Run Coding → Test → Review with a single retry on failure."""
        max_retries = max(0, int(context.config.get("max_retries", 1)))
        attempt = 0

        while True:
            context = await self.coding_step.run(context)
            context = await self.test_step.run(context)
            context = await self.review_step.run(context)

            tests_pass = context.test.success if context.test else False
            review_pass = context.review.decision == "approved" if context.review else False

            if tests_pass and review_pass:
                break

            if attempt >= max_retries:
                print("Retry limit reached; stopping after failed test/review.")
                break

            attempt += 1
            reason = []
            if not tests_pass:
                reason.append("tests failed")
            if not review_pass:
                reason.append("review rejected")
            reason_text = ", ".join(reason) if reason else "unknown reason"
            print(f"Retrying coding/test/review (attempt {attempt} of {max_retries}) after {reason_text}...")

        return context

    def _print_summary(self, context: WorkflowContext) -> None:
        """Print workflow execution summary."""
        print(f"\n{'='*60}")
        print(f"WORKFLOW SUMMARY")
        print(f"{'='*60}")
        print(f"Run ID: {context.run_id}")
        print(f"Ticket: {context.ticket.ticket_id if context.ticket else 'N/A'}")
        print(f"Started: {context.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Completed: {context.completed_at.strftime('%Y-%m-%d %H:%M:%S') if context.completed_at else 'Not completed'}")

        if context.completed_at:
            duration = (context.completed_at - context.started_at).total_seconds()
            print(f"Duration: {duration:.2f}s")

        print(f"\nCompleted Steps ({len(context.completed_steps)}):")
        for step in context.completed_steps:
            print(f"  ✓ {step}")

        if context.errors:
            print(f"\nErrors ({len(context.errors)}):")
            for error in context.errors:
                print(f"  ✗ {error}")

        if context.pr:
            print(f"\nPull Request:")
            print(f"  Branch: {context.pr.branch_name}")
            print(f"  URL: {context.pr.pr_url}")

        if context.review:
            print(f"\nReview Decision: {context.review.decision.upper()}")

        status = "SUCCESS" if context.is_successful() else "FAILED"
        print(f"\nStatus: {status}")
        print(f"{'='*60}\n")

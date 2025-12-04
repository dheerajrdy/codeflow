"""Workflow step definitions."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict

from src.integrations import apply_patch, run_tests
from .context import WorkflowContext, TicketInfo, RepoInfo, DesignOutput, CodingOutput, TestOutput, ReviewOutput, PRInfo, NotesOutput


class WorkflowStep(ABC):
    """Base class for workflow steps."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Execute the step and return updated context."""
        pass

    async def run(self, context: WorkflowContext) -> WorkflowContext:
        """Run the step with error handling and logging."""
        print(f"\n{'='*60}")
        print(f"STEP: {self.name}")
        print(f"{'='*60}")

        context.current_step = self.name
        if hasattr(context, "add_log"):
            context.add_log(f"START {self.name}")

        try:
            context = await self.execute(context)
            context.mark_step_complete(self.name)
            print(f"✓ {self.name} completed successfully")
            if hasattr(context, "add_log"):
                context.add_log(f"END {self.name} SUCCESS")
        except Exception as e:
            error_msg = f"Error in {self.name}: {str(e)}"
            print(f"✗ {error_msg}")
            context.add_error(error_msg)
            if hasattr(context, "add_log"):
                context.add_log(f"END {self.name} FAILURE: {error_msg}")
            raise

        return context


class FetchTicketStep(WorkflowStep):
    """Fetch ticket details from Jira."""

    def __init__(self, jira_client=None):
        super().__init__("FetchTicket")
        self.jira_client = jira_client

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Fetch ticket details (real Jira if configured, otherwise stub)."""
        # For now, create a dummy ticket
        ticket_id = context.config.get("ticket_id", "UNKNOWN")

        print(f"  Fetching ticket: {ticket_id}")

        if self.jira_client:
            print(f"  Using Jira client to fetch ticket data")
            try:
                context.ticket = await self.jira_client.fetch_ticket(ticket_id)
            except Exception as exc:
                context.add_error(f"Failed to fetch ticket {ticket_id}: {exc}")
                raise
        else:
            print(f"  [STUB] Would call Jira API here")
            context.ticket = TicketInfo(
                ticket_id=ticket_id,
                title=f"[STUB] Implement feature X for ticket {ticket_id}",
                description="This is a stub ticket description with some details about the feature.",
                acceptance_criteria="1. Feature works\n2. Tests pass\n3. Code is clean"
            )

        print(f"  Title: {context.ticket.title}")
        print(f"  Description: {context.ticket.description[:60]}...")

        return context


class AnalyzeRepoStep(WorkflowStep):
    """Analyze repository metadata."""

    def __init__(self):
        super().__init__("AnalyzeRepo")

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Analyze repository (stubbed for Day 1)."""
        print(f"  Analyzing repository...")

        repo_root = context.config.get("repo_path") or str(Path().resolve())
        main_language = context.config.get("main_language", "Python")
        test_command = context.config.get("test_command", "pytest")
        repo_url = context.config.get("repo_url", "https://github.com/example/repo")
        default_branch = context.config.get("default_branch", "main")

        context.repo = RepoInfo(
            repo_path=repo_root,
            main_language=main_language,
            test_command=test_command,
            repo_url=repo_url,
            default_branch=default_branch,
        )

        print(f"  Language: {context.repo.main_language}")
        print(f"  Test Command: {context.repo.test_command}")

        return context


class DesignStep(WorkflowStep):
    """Run Design Agent to create implementation plan."""

    def __init__(self, design_agent=None):
        super().__init__("Design")
        self.design_agent = design_agent
        self.use_stub = design_agent is None

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Run Design Agent."""
        print(f"  Running Design Agent...")

        if self.use_stub:
            # Use stub implementation (Day 1 mode)
            print(f"  [STUB] Would call Design Agent with ticket + repo info")

            context.design = DesignOutput(
                problem_understanding=f"Need to implement: {context.ticket.title}",
                proposed_approach="1. Create new module\n2. Add tests\n3. Update docs",
                target_files=["src/agents/new_feature.py", "tests/test_new_feature.py"],
                step_by_step_plan=[
                    "Create src/agents/new_feature.py",
                    "Implement core functionality",
                    "Add unit tests",
                    "Update documentation"
                ]
            )
        else:
            # Use real Design Agent (Day 2+)
            print(f"  Calling Design Agent with ticket + repo info")
            context.design = await self.design_agent.run(
                ticket_info=context.ticket,
                repo_info=context.repo,
            )

        print(f"  Target Files: {', '.join(context.design.target_files)}")
        print(f"  Plan has {len(context.design.step_by_step_plan)} steps")

        return context


class CodingStep(WorkflowStep):
    """Run Coding Agent to generate code changes."""

    def __init__(self, coding_agent=None):
        super().__init__("Coding")
        self.coding_agent = coding_agent
        self.use_stub = coding_agent is None

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Run Coding Agent."""
        print(f"  Running Coding Agent...")

        if self.use_stub:
            print(f"  [STUB] Would call Coding Agent with design plan")

            context.coding = CodingOutput(
                diff="[STUB DIFF]\n+++ src/agents/new_feature.py\n+def new_function():\n+    pass",
                files_changed=context.design.target_files if context.design else [],
                explanations="Added new_function() to implement the feature",
            )
        else:
            # Build lightweight code context for target files
            repo_root = Path(context.repo.repo_path or ".") if context.repo else Path(".")
            target_files = context.design.target_files if context.design else []
            code_context = self._load_code_context(repo_root, target_files)

            context.coding = await self.coding_agent.run(
                ticket_info=context.ticket,
                design_output=context.design,
                repo_info=context.repo,
                code_context=code_context,
            )

            if not context.coding.files_changed and target_files:
                context.coding.files_changed = target_files

            # Apply the generated patch to the working tree unless in dry-run mode
            if context.coding.diff:
                if context.dry_run:
                    print(f"  [DRY RUN] Skipping patch application")
                else:
                    success, output = apply_patch(str(repo_root), context.coding.diff)
                    if not success:
                        raise RuntimeError(f"Failed to apply patch: {output}")

        print(f"  Files Changed: {len(context.coding.files_changed)}")
        if context.coding.diff:
            preview = context.coding.diff[:120].replace("\n", " ")
            print(f"  Diff Preview: {preview}...")

        return context

    def _load_code_context(self, repo_root: Path, target_files: list[str]) -> Dict[str, str]:
        """Load code snippets for target files to help the coding agent."""
        context: Dict[str, str] = {}
        for path in target_files:
            file_path = repo_root / path
            if not file_path.exists() or not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
                if len(content) > 5000:
                    content = content[:5000] + "\n... [truncated]"
                context[path] = content
            except OSError:
                continue
        return context


class TestStep(WorkflowStep):
    """Run tests on the code changes."""

    def __init__(self):
        super().__init__("Test")

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Run tests using configured command."""
        command = context.repo.test_command if context.repo else "pytest"
        repo_root = context.repo.repo_path if context.repo else "."

        print(f"  Running tests: {command}")

        if context.dry_run:
            context.test = TestOutput(
                success=True,
                output=f"[DRY RUN] Skipped tests ({command})",
                errors="",
                duration_seconds=0.0,
            )
        else:
            success, output, errors, duration = run_tests(repo_root, command)
            context.test = TestOutput(
                success=success,
                output=output,
                errors=errors,
                duration_seconds=duration,
            )

        print(f"  Test Result: {'PASS' if context.test.success else 'FAIL'}")
        print(f"  Duration: {context.test.duration_seconds}s")

        return context


class ReviewStep(WorkflowStep):
    """Run Review Agent to evaluate changes."""

    def __init__(self, review_agent=None):
        super().__init__("Review")
        self.review_agent = review_agent
        self.use_stub = review_agent is None

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Run Review Agent."""
        print(f"  Running Review Agent...")

        if self.use_stub:
            # Use stub implementation (Day 1 mode)
            print(f"  [STUB] Would call Review Agent with diff + test results")

            # Auto-approve if tests passed (for Day 1 stub)
            decision = "approved" if context.test.success else "rejected"

            context.review = ReviewOutput(
                decision=decision,
                comments=[
                    "Code changes look good",
                    "Tests are passing",
                    "Meets acceptance criteria"
                ],
                suggestions=["Consider adding more edge case tests"]
            )
        else:
            # Use real Review Agent (Day 2+)
            print(f"  Calling Review Agent with diff + test results")
            context.review = await self.review_agent.run(
                ticket_info=context.ticket,
                design_output=context.design,
                diff=context.coding.diff,
                test_output=context.test,
            )

        print(f"  Decision: {context.review.decision.upper()}")
        print(f"  Comments: {len(context.review.comments)} items")

        return context


class CreatePRStep(WorkflowStep):
    """Create pull request on GitHub."""

    def __init__(self, github_client=None, auto_confirm: bool = False):
        super().__init__("CreatePR")
        self.github_client = github_client
        self.auto_confirm = auto_confirm

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Create PR using GitHub client (stub if not configured)."""
        # Only create PR if review approved
        if not context.review or context.review.decision != "approved":
            print(f"  Skipping PR creation - review not approved")
            return context

        branch_name = f"feature/{context.ticket.ticket_id}" if context.ticket else "feature/auto-branch"
        pr_title = f"{context.ticket.ticket_id}: {context.ticket.title}" if context.ticket else "Automated change"
        pr_body = self._build_pr_body(context)

        if context.dry_run or not self.github_client:
            if context.dry_run:
                print(f"  [DRY RUN] Would create PR but skipping in dry-run mode")
            else:
                print(f"  [STUB] GitHub client not configured; returning placeholder PR info")
            context.pr = PRInfo(
                branch_name=branch_name,
                pr_url=f"https://github.com/example/repo/pull/{context.ticket.ticket_id if context.ticket else 'draft'}",
                pr_number=None,
            )
            return context

        print(f"  Creating branch {branch_name} and opening PR...")
        if not self.auto_confirm:
            if not self._confirm(f"Proceed with git actions for {branch_name} and open PR? [y/N]: "):
                context.add_error("User declined PR creation")
                return context

        try:
            await self.github_client.create_branch(
                branch_name,
                base_branch=context.repo.default_branch if context.repo else None,
            )

            await self.github_client.commit_all(pr_title)
            await self.github_client.push_branch(branch_name)

            pr_info = await self.github_client.create_pull_request(
                branch_name=branch_name,
                title=pr_title,
                body=pr_body,
            )

            context.pr = pr_info
        except Exception as exc:
            context.add_error(f"PR creation failed: {exc}")
            raise

        print(f"  Branch: {context.pr.branch_name}")
        print(f"  PR URL: {context.pr.pr_url}")

        return context

    def _build_pr_body(self, context: WorkflowContext) -> str:
        """Create a simple PR body summarizing the change."""
        design_summary = context.design.proposed_approach if context.design else ""
        test_summary = context.test.output if context.test else ""
        return (
            f"## Summary\n{design_summary}\n\n"
            f"## Testing\n{test_summary or 'Tests not run'}\n"
        )

    def _confirm(self, prompt: str) -> bool:
        """Prompt user for confirmation unless auto-confirm is enabled."""
        try:
            reply = input(prompt).strip().lower()
            return reply in ("y", "yes")
        except EOFError:
            return False


class NotesStep(WorkflowStep):
    """Run Notes/Metadata Agent to capture learnings."""

    def __init__(self, notes_agent=None):
        super().__init__("Notes")
        self.notes_agent = notes_agent
        self.use_stub = notes_agent is None

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Run Notes Agent."""
        print(f"  Running Notes Agent...")

        if self.use_stub:
            print(f"  [STUB] Would call Notes Agent with full context")

            context.notes = NotesOutput(
                summary=f"Processed {context.ticket.ticket_id if context.ticket else 'N/A'}.",
                lessons_learned=[
                    "Workflow completed successfully",
                    "All tests passed on first attempt"
                ],
                suggestions=[
                    "Consider adding integration tests",
                    "Update documentation"
                ],
                tags=["feature", "success", (context.repo.main_language.lower() if context.repo else "unknown")]
            )
        else:
            ticket_summary = (
                f"{context.ticket.ticket_id}: {context.ticket.title}"
                if context.ticket
                else "No ticket"
            )
            design_summary = context.design.proposed_approach if context.design else "No design data"
            coding_summary = (
                f"Files: {', '.join(context.coding.files_changed)}; Diff size: {len(context.coding.diff)}"
                if context.coding
                else "No coding output"
            )
            test_summary = (
                f"{'PASS' if context.test.success else 'FAIL'} - {context.test.output or context.test.errors}"
                if context.test
                else "Tests not run"
            )
            review_summary = (
                f"{context.review.decision.upper()} ({len(context.review.comments)} comments)"
                if context.review
                else "Review not run"
            )
            pr_summary = (
                f"{context.pr.pr_url} on {context.pr.branch_name}"
                if context.pr
                else "PR not created"
            )
            logs = "\n".join(context.logs) if context.logs else ""

            context.notes = await self.notes_agent.run(
                ticket_summary=ticket_summary,
                design_summary=design_summary,
                coding_summary=coding_summary,
                test_summary=test_summary,
                review_summary=review_summary,
                pr_summary=pr_summary,
                logs=logs,
            )

        print(f"  Summary: {context.notes.summary}")
        print(f"  Lessons: {len(context.notes.lessons_learned)} items")
        print(f"  Tags: {', '.join(context.notes.tags)}")

        return context

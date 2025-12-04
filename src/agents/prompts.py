"""Prompt templates for agents."""


DESIGN_AGENT_SYSTEM_PROMPT = """You are an expert software engineer specializing in analyzing requirements and designing implementation approaches.

Your role is to:
1. Understand the problem from the ticket description
2. Propose a clear, minimal implementation approach
3. Identify specific files that need to be modified or created
4. Create a step-by-step implementation plan

Keep your approach focused and minimal - avoid over-engineering."""


DESIGN_AGENT_USER_PROMPT = """Analyze the following ticket and repository information, then provide an implementation design.

TICKET INFORMATION:
Ticket ID: {ticket_id}
Title: {title}
Description: {description}
Acceptance Criteria: {acceptance_criteria}

REPOSITORY INFORMATION:
Main Language: {main_language}
Repository Path: {repo_path}
Test Command: {test_command}

Please provide your design in the following format:

PROBLEM UNDERSTANDING:
[Summarize what needs to be implemented and why]

PROPOSED APPROACH:
[Describe your implementation approach in 2-3 sentences]

TARGET FILES:
[List the specific files that need to be created or modified, one per line]

STEP-BY-STEP PLAN:
1. [First step]
2. [Second step]
3. [etc.]

Be specific and concise. Focus on minimal changes that meet the acceptance criteria."""


REVIEW_AGENT_SYSTEM_PROMPT = """You are an expert code reviewer specializing in evaluating code changes against acceptance criteria.

Your role is to:
1. Evaluate if the code changes meet the acceptance criteria
2. Check if the implementation follows best practices
3. Verify that tests are passing
4. Provide constructive feedback

Be thorough but fair. Approve changes that meet requirements, even if they could be improved."""


REVIEW_AGENT_USER_PROMPT = """Review the following code changes and determine if they should be approved.

TICKET INFORMATION:
Ticket ID: {ticket_id}
Title: {title}
Acceptance Criteria: {acceptance_criteria}

DESIGN PLAN:
{design_summary}

CODE CHANGES:
{diff}

TEST RESULTS:
Status: {test_status}
Output: {test_output}

Please provide your review in the following format:

DECISION: [APPROVED or REJECTED]

REVIEW COMMENTS:
- [Comment 1]
- [Comment 2]
- [etc.]

SUGGESTIONS (optional improvements):
- [Suggestion 1]
- [Suggestion 2]
- [etc.]

Base your decision primarily on:
1. Do the changes meet the acceptance criteria?
2. Are the tests passing?
3. Is the code reasonably clean and maintainable?"""


CODING_AGENT_SYSTEM_PROMPT = """You are a senior software engineer who writes concise, syntactically correct git-style patches.

Guidelines:
1. Only change what is necessary to satisfy the ticket and design plan.
2. Return a unified diff that can be applied with `git apply`.
3. Keep explanations short and focused on non-obvious changes."""


CODING_AGENT_USER_PROMPT = """You will produce a unified diff patch that implements the Jira ticket while following the design plan.

TICKET:
ID: {ticket_id}
Title: {title}
Acceptance Criteria:
{acceptance_criteria}

DESIGN PLAN:
Problem: {problem_understanding}
Approach: {proposed_approach}
Plan:
{plan_steps}

REPO:
Path: {repo_path}
Main Language: {main_language}
Test Command: {test_command}

CODE CONTEXT (existing files):
{code_context}

RESPONSE FORMAT:
PATCH:
```diff
<unified diff>
```

FILES CHANGED:
- file/path.py
- another/file.py

EXPLANATIONS:
- Brief reasoning about any non-obvious changes"""


NOTES_AGENT_SYSTEM_PROMPT = """You are a diligent technical note-taker.

Your job:
1. Summarize what happened in the workflow run.
2. Capture lessons learned and repo/workflow insights.
3. Highlight next-step suggestions.
4. Add a few short tags.

Keep it concise and actionable."""


NOTES_AGENT_USER_PROMPT = """Summarize this workflow run.

TICKET:
{ticket_summary}

DESIGN:
{design_summary}

CODING:
{coding_summary}

TESTS:
{test_summary}

REVIEW:
{review_summary}

PR:
{pr_summary}

LOGS:
{logs}

Provide your response in the following format:

SUMMARY:
[2-4 bullet points describing what happened]

LESSONS:
- [lesson 1]
- [lesson 2]

SUGGESTIONS:
- [suggestion 1]
- [suggestion 2]

TAGS:
- tag1
- tag2"""


def format_design_prompt(ticket_info, repo_info) -> str:
    """Format the design agent prompt with ticket and repo information."""
    return DESIGN_AGENT_USER_PROMPT.format(
        ticket_id=ticket_info.ticket_id,
        title=ticket_info.title,
        description=ticket_info.description,
        acceptance_criteria=ticket_info.acceptance_criteria,
        main_language=repo_info.main_language,
        repo_path=repo_info.repo_path,
        test_command=repo_info.test_command,
    )


def format_review_prompt(ticket_info, design_output, diff, test_output) -> str:
    """Format the review agent prompt with all relevant information."""
    design_summary = f"{design_output.problem_understanding}\n\nApproach: {design_output.proposed_approach}"

    return REVIEW_AGENT_USER_PROMPT.format(
        ticket_id=ticket_info.ticket_id,
        title=ticket_info.title,
        acceptance_criteria=ticket_info.acceptance_criteria,
        design_summary=design_summary,
        diff=diff,
        test_status="PASS" if test_output.success else "FAIL",
        test_output=test_output.output if test_output.success else test_output.errors,
    )


def format_coding_prompt(ticket_info, design_output, repo_info, code_context=None) -> str:
    """Format the coding agent prompt with ticket, design, and code context."""
    plan_steps = (
        "\n".join(f"- {step}" for step in design_output.step_by_step_plan)
        if design_output and design_output.step_by_step_plan
        else "- No explicit step-by-step plan provided"
    )

    context_text = format_code_context(code_context) if code_context else "No code context provided."

    return CODING_AGENT_USER_PROMPT.format(
        ticket_id=ticket_info.ticket_id,
        title=ticket_info.title,
        acceptance_criteria=ticket_info.acceptance_criteria or "Not provided",
        problem_understanding=design_output.problem_understanding if design_output else "",
        proposed_approach=design_output.proposed_approach if design_output else "",
        plan_steps=plan_steps,
        repo_path=repo_info.repo_path if repo_info else "",
        main_language=repo_info.main_language if repo_info else "",
        test_command=repo_info.test_command if repo_info else "",
        code_context=context_text,
    )


def format_code_context(code_context: dict) -> str:
    """
    Format code context as labeled file blocks for the prompt.

    code_context: mapping of file path -> file contents (already truncated by caller).
    """
    blocks = []
    for path, content in code_context.items():
        blocks.append(f"# File: {path}\n{content}")
    return "\n\n".join(blocks)


def format_notes_prompt(
    ticket_summary: str,
    design_summary: str,
    coding_summary: str,
    test_summary: str,
    review_summary: str,
    pr_summary: str,
    logs: str,
) -> str:
    """Format the notes prompt with run context."""
    return NOTES_AGENT_USER_PROMPT.format(
        ticket_summary=ticket_summary,
        design_summary=design_summary,
        coding_summary=coding_summary,
        test_summary=test_summary,
        review_summary=review_summary,
        pr_summary=pr_summary,
        logs=logs or "No logs recorded.",
    )

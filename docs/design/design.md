
Below is:
	1.	A 6-day plan (what to do each day, including how you’ll use Claude Code).
	2.	A concrete design doc you can drop into your repo as docs/design/multi_agent_coding_workflow.md.

⸻

1. Six-day execution plan

Day 1 – Problem framing & scaffolding

Goals
	•	Clarify scope and “happy path”.
	•	Set up project skeleton + basic workflow runner.
	•	Make this feel real in your dev environment.

Tasks
	1.	Define v1 “happy path” workflow
For a single Jira project + GitHub repo:
	1.	Select a Jira ticket ID.
	2.	Pull ticket details (title, description, acceptance criteria).
	3.	Pull repo (or ensure local clone) and basic metadata (main language, test command).
	4.	Run workflow:
	•	Design Agent → proposed plan + file-level impact.
	•	Coding Agent → patch/diff.
	•	Review Agent → comments + approve/reject.
	5.	If approved → create branch + PR + comment back to Jira with link.
	6.	Log metadata + learning notes.
	2.	Create repo structure
Something like:

/src
  /agents
    design_agent.py
    coding_agent.py
    review_agent.py
    notes_agent.py
  /orchestration
    workflow_engine.py
    steps.py
  /integrations
    jira_client.py
    github_client.py
    vcs_utils.py
  /models
    model_client.py
/tests
/docs
  design/


	3.	Wire minimal workflow engine
	•	A small sequential workflow runner that runs named steps in order and passes a shared context object.
	•	CLI entrypoint, e.g.:

python -m src.cli.run_workflow --ticket JIRA-123


	4.	Use Claude Code
	•	Ask Claude to scaffold the project layout, workflow runner, and context object.
	•	Have it write the CLI and a first version of workflow_engine.py.

Day 1 deliverables
	•	Repo initialized with skeleton structure.
	•	Basic workflow runner that prints stubbed results for each step.
	•	Draft of the design doc file created (we’ll fill it in from below).

⸻

Day 2 – Model & agent interfaces

Goals
	•	Define agent interfaces and model abstraction.
	•	Implement Design Agent & Review Agent as stubs that just reason on text.

Tasks
	1.	Define ModelClient abstraction
	•	Methods like:

class ModelClient(Protocol):
    def chat(self, messages: List[Message], tools: Optional[List[Tool]] = None) -> ModelResponse: ...


	•	Implementation backed by the SDK you choose (Gemini/Claude/etc.) – but keep this simple for now.

	2.	Implement Design Agent
	•	Input: ticket details + summary of repo (just text for now).
	•	Output:
	•	problem understanding,
	•	proposed approach,
	•	list of target files/functions,
	•	step-by-step plan.
	•	Use prompt templates stored in code or yaml (so you can tweak later).
	3.	Implement Review Agent
	•	Input: ticket details + patch/diff + tests summary.
	•	Output:
	•	review comments,
	•	pass/fail decision,
	•	suggested changes.
	4.	Add agents into workflow
	•	Update the workflow so step 1 = DesignAgent, step 3 = ReviewAgent (coding will be stubbed until tomorrow).
	5.	Use Claude Code
	•	Ask Claude to:
	•	implement the ModelClient abstraction,
	•	write a first pass at DesignAgent and ReviewAgent using prompt templates,
	•	hook them into the workflow.

Day 2 deliverables
	•	ModelClient abstraction.
	•	DesignAgent and ReviewAgent implemented (talking to a real model).
	•	Workflow now runs: ticket → design → review (with dummy patch).

⸻

Day 3 – Coding Agent & GitHub/Jira wiring (happy path)

Goals
	•	Implement Coding Agent that operates on the local repo and generates patches.
	•	Integrate GitHub and Jira for real data.
	•	Complete the end-to-end happy path for simple tickets.

Tasks
	1.	Implement Coding Agent
	•	Input:
	•	ticket details,
	•	design output (plan + target files),
	•	repo context (e.g., file contents or summaries).
	•	Output:
	•	patches/diffs (e.g., unified diff or a structured “file → updated content” mapping).
	•	Use a code-generation prompt + maybe a separate prompt to clean up/format.
	2.	Local code operations
	•	Helper functions:
	•	apply patch to working tree,
	•	run tests with configurable command (e.g., pytest, npm test),
	•	collect test output.
	3.	Integrate GitHub
	•	Personal Access Token or other auth.
	•	Functions:
	•	create branch with conventional naming,
	•	push commits,
	•	open PR with title & body from agents.
	4.	Integrate Jira
	•	Read ticket details by key.
	•	Optionally: comment on ticket with link to PR once created.
	5.	Wire full workflow
	•	Steps (simplified):
	1.	FetchTicketStep
	2.	AnalyzeRepoStep (basic repo metadata)
	3.	DesignStep
	4.	CodingStep (apply patch locally)
	5.	TestStep (run tests)
	6.	ReviewStep
	7.	CreatePRStep (if approved)
	6.	Use Claude Code
	•	Have Claude write:
	•	GitHub client (branch, push, PR create),
	•	Jira client,
	•	CodingAgent and TestStep mapping.

Day 3 deliverables
	•	First end-to-end flow: from Jira ticket → PR open on GitHub (for simple tickets), even if fragile.
	•	CLI command that runs the workflow for a given ticket key.

⸻

Day 4 – Notes/metadata agent + observability

Goals
	•	Add a Notes/Metadata Agent for “learning experience”.
	•	Improve logs and traceability so you can see what’s going on.

Tasks
	1.	Define data model for metadata
	•	For each workflow run, store:
	•	ticket ID, repo, branch, timestamps,
	•	decisions from each agent,
	•	test results,
	•	PR URL,
	•	“learning notes” (what worked, what failed, patterns about the codebase).
	2.	Notes/Metadata Agent
	•	Input: full run context (agents’ outputs, logs).
	•	Output:
	•	human-readable “run summary”,
	•	suggestions for better prompts or workflow tweaks,
	•	repo-specific knowledge (e.g., “Tests live under tests/ and are slow”).
	•	Store in a simple format:
	•	local JSONL file, or
	•	SQLite, or
	•	simple text files under /runs.
	3.	Observability
	•	Add consistent logging:
	•	Each step logs start/end and key outputs.
	•	Optionally, log model tokens and cost estimates (even if rough).
	•	Add a --dry-run mode that prints what would happen without touching git.
	4.	Use Claude Code
	•	Let Claude:
	•	implement the notes agent,
	•	create logging decorators or a small run_logger module,
	•	add a simple “show last N runs” CLI command.

Day 4 deliverables
	•	Notes/Metadata Agent implemented and wired in as final step.
	•	Persistent log of each workflow run with a human-readable summary.
	•	Better debug-ability via logs.

⸻

Day 5 – Hardening, guardrails, & UX polish

Goals
	•	Reduce “footguns”.
	•	Make it nicer to run and experiment with.

Tasks
	1.	Guardrails & safety checks
	•	Confirm with user before:
	•	creating branches,
	•	pushing code,
	•	opening PRs (or allow --no-confirm for full automation).
	•	Handle failure cases:
	•	Jira ticket not found,
	•	tests fail,
	•	Review Agent rejects patch.
	•	Add conditional branches:
	•	On test failure → ask Coding Agent to fix based on test output (loop once).
	•	On review rejection → one retry cycle only, to avoid infinite loops.
	2.	Better CLI UX
	•	Example commands:

# Run full workflow for one ticket
codeflow run JIRA-123

# Dry-run
codeflow run JIRA-123 --dry-run

# Show last runs
codeflow runs list


	3.	Configuration
	•	Simple config file (e.g., config.yaml):
	•	Jira base URL + project.
	•	GitHub org/repo.
	•	Default test command.
	•	Model config (provider, model name, temperature).
	4.	Use Claude Code
	•	Have Claude:
	•	add argument parsing & subcommands,
	•	implement failure handling branches,
	•	clean up error messages and user prompts.

Day 5 deliverables
	•	Guardrails & basic error handling.
	•	A nicer CLI experience.
	•	Config-driven setup so you can reuse with new repos.

⸻

Day 6 – Evaluation, examples & learning-focused polish

Goals
	•	Add some light evaluation and examples.
	•	Document how you should use and extend the system.

Tasks
	1.	Create a small evaluation set
	•	Hand-pick 3–5 “training” Jira tickets (or fake ones) that:
	•	are small but representative,
	•	have known good solutions.
	•	For each, record:
	•	success/failure of workflow,
	•	manual notes (what the agent missed, what was good).
	2.	Add evaluation harness
	•	CLI command like:

codeflow eval --tickets JIRA-1,JIRA-2,JIRA-3


	•	Collect metrics:
	•	finished successfully (yes/no),
	•	tests passing,
	•	review pass/fail,
	•	maybe a short human score (1–5).

	3.	Docs for learning
	•	In the design doc, add:
	•	“How to extend agents” section (e.g., add Test Agent, Lint Agent).
	•	“Prompt iteration tips” for Design/Coding/Review Agents.
	•	“What to inspect after each run” – tie into your Notes Agent.
	4.	Use Claude Code
	•	Ask Claude to:
	•	generate the evaluation harness,
	•	write example configs and sample tickets,
	•	help polish documentation.

Day 6 deliverables
	•	Basic eval harness and 3–5 example tickets.
	•	Updated design doc with “how to extend/learn from this”.
	•	A system you can run, inspect, and improve.

⸻

2. Design doc you can use (v1)

You can more or less copy-paste this into docs/design/multi_agent_coding_workflow.md and tweak.

⸻

1. Overview

We are building a multi-agent, workflow-based coding assistant that:
	•	Takes a Jira ticket as input.
	•	Understands and designs a solution.
	•	Generates code changes in a GitHub repo.
	•	Runs tests and performs automated review.
	•	Opens a PR and posts a summary back to Jira.
	•	Captures metadata and learning notes about each run.

The system is designed as a learning tool for the developer (Dheeraj) and as a foundation for future extensions (more agents, more repos, more sophisticated evaluation).

⸻

2. Goals & non-goals

Goals
	•	Automate the happy path from Jira ticket → PR for small/medium tasks.
	•	Provide clear, inspectable multi-agent workflows (Design, Coding, Review, Notes).
	•	Be easy to iterate on prompts and agent behavior.
	•	Log metadata and learning notes for each run.

Non-goals (for v1)
	•	Full generality across any codebase, language, or monorepo.
	•	Sophisticated AI-based evaluation (we’ll rely on tests + simple metrics).
	•	Multi-repo changes or cross-service coordination.
	•	Rich web UI (CLI-first is fine).

⸻

3. Key workflows

3.1 Core workflow: “Implement Jira ticket and open PR”
	1.	Select ticket
	•	Input: Jira ticket key (PROJECT-123).
	•	System fetches ticket details via Jira API.
	2.	Analyze repo
	•	Determine language(s).
	•	Optionally compute lightweight metadata (e.g., directories, key config files).
	•	(Future: vector index of code for semantic search.)
	3.	Design phase (Design Agent)
	•	Model reads ticket + basic repo info.
	•	Outputs:
	•	Problem understanding.
	•	Proposed approach.
	•	List of candidate files/areas to change.
	•	Step-by-step plan.
	4.	Coding phase (Coding Agent)
	•	Model receives ticket + design + relevant code snippets.
	•	Proposes code changes as patches/diffs.
	•	System applies patch to local repo.
	5.	Testing phase
	•	Run project’s test command (configurable).
	•	Collect results + logs.
	6.	Review phase (Review Agent)
	•	Model sees ticket, design, diff, and test results.
	•	Outputs:
	•	Pass/fail decision.
	•	Review comments.
	•	(Optional) suggested improvements.
	7.	PR creation
	•	If review passes:
	•	Create branch.
	•	Commit changes.
	•	Push branch and open PR on GitHub.
	•	Write PR description using model output.
	•	Optionally comment back to Jira with PR link.
	8.	Notes & metadata (Notes Agent)
	•	Generates:
	•	Run summary (“what happened”).
	•	Lessons learned/patterns about the repo.
	•	Suggestions for future prompt/workflow improvements.
	•	Persist to local store (JSONL/SQLite).

3.2 Evaluation workflow
	•	Run the above workflow on a small set of known tickets.
	•	Record metrics (success, tests pass, review passes, manual score).
	•	Use notes to iterate on prompts and configuration.

⸻

4. Architecture

4.1 Components
	•	CLI (codeflow or similar)
	•	Entrypoint for users to run workflows and view past runs.
	•	Workflow Engine
	•	Executes a sequence of steps with a shared WorkflowContext.
	•	Supports:
	•	Sequential execution (v1),
	•	Simple conditionals (e.g., on test failure),
	•	Retry policies per step.
	•	Agents
	•	Design Agent
	•	Coding Agent
	•	Review Agent
	•	Notes/Metadata Agent
	•	Integrations
	•	Jira Client
	•	Fetch ticket details.
	•	(Optional) Post comments.
	•	GitHub Client
	•	Create branches, commits, and PRs.
	•	VCS Utils
	•	Apply patches,
	•	Run tests,
	•	Inspect git status.
	•	Model Layer
	•	ModelClient interface with one concrete implementation (backed by your chosen SDK).
	•	Encapsulates:
	•	chat/completion,
	•	optional tool-calling if needed later.
	•	Storage
	•	Config: config.yaml.
	•	Run logs/metadata: local files or small DB.
	•	(Future) Code embeddings index.

4.2 Orchestration pattern
We’re using a workflow pattern (explicit orchestration):
	•	Sequential steps:
	•	FetchTicket → AnalyzeRepo → Design → Code → Test → Review → PR → Notes.
	•	Conditional branches:
	•	If tests fail → optional retry loop to Coding Agent with test output.
	•	If Review Agent rejects patch → optional retry loop.
	•	If still failing → abort and record failure.

This keeps control flow transparent and easy to reason about, versus a free-form group chat.

⸻

5. Agent definitions

5.1 Design Agent
	•	Inputs
	•	Jira ticket (title, description, acceptance criteria).
	•	Basic repo info (main language, root-level structure, key files as snippets).
	•	Outputs
	•	Problem restatement.
	•	Proposed implementation approach.
	•	Target files/modules.
	•	Step-by-step plan.
	•	Key concerns
	•	Avoid over-scoping changes.
	•	Reference acceptance criteria explicitly.

5.2 Coding Agent
	•	Inputs
	•	Ticket.
	•	Design Agent output.
	•	Code snippets from candidate files.
	•	Any repo conventions (test command, style).
	•	Outputs
	•	Code changes as patches/diffs.
	•	Possibly small explanations of non-obvious changes.
	•	Key concerns
	•	Generate minimal necessary changes.
	•	Keep code syntactically correct and idiomatic.

5.3 Review Agent
	•	Inputs
	•	Ticket.
	•	Design output.
	•	Diff.
	•	Test results.
	•	Outputs
	•	Decision: approve / request changes.
	•	Review comments aligned with acceptance criteria.
	•	Optional suggestions for improvement.

5.4 Notes/Metadata Agent
	•	Inputs
	•	Full workflow context:
	•	Steps run, outputs, errors.
	•	Tests, review decisions, PR link.
	•	Outputs
	•	Human-readable summary (for you).
	•	Extracted “lessons learned” about:
	•	The repo (e.g., structure, pitfalls).
	•	The workflow (where it struggled).
	•	Tags/labels (e.g., “routing issue”, “test flakiness”).

⸻

6. Models & SDK
	•	Model abstraction: ModelClient.
	•	Initial model choice:
	•	One primary model (e.g., Claude or Gemini), accessed via the chosen SDK.
	•	Future:
	•	Add a second ModelClient for a “deep debug” agent if needed.
	•	Configuration:
	•	Model name, temperature, max tokens defined in config.yaml.

⸻

7. Data, storage & configuration
	•	config.yaml:
	•	Jira base URL, project key, API token env var.
	•	GitHub org/repo, token env var.
	•	Test command (e.g., "pytest").
	•	Model configuration.
	•	Run store:
	•	runs/ directory or SQLite DB storing:
	•	run_id, ticket_id, timestamps,
	•	step results,
	•	PR URL,
	•	notes from Notes Agent.

⸻

8. Evaluation & iteration
	•	Eval set:
	•	3–5 tickets (real or synthetic) with known good solutions.
	•	Metrics:
	•	End-to-end success (PR created, tests pass).
	•	Review pass/fail (automated).
	•	Manual rating (1–5) for quality.
	•	Process:
	•	Run eval set after significant changes.
	•	Use Notes Agent output + your manual notes to adjust:
	•	prompts,
	•	step ordering,
	•	retry logic,
	•	maybe split more specialized agents later.

⸻

9. Risks & open questions
	•	Risk: Model may hallucinate file names or APIs.
	•	Mitigation: constrain with real file lists, use explicit prompts to avoid new files unless asked.
	•	Risk: Over-large diffs.
	•	Mitigation: ask Coding Agent to keep changes minimal, limit patch size for v1.
	•	Risk: Excessive complexity in workflows.
	•	Mitigation: stay with simple sequential workflows at first, only add more branches when pain points are clear.
	•	Open questions (for later, not blocking v1):
	•	Should we add a dedicated Test/Lint Agent?
	•	Should we build a small web UI later?
	•	When to introduce a second model for deep debugging?

⸻
Good question to pause on now. Let’s line up what we’re actually applying from the “Designing Multi-Agent Systems” book + SKILL, and what we’re intentionally leaving on the shelf (for later or never).

I’ll split it into Using Now vs De-prioritized / Later.

⸻

1. Concepts we are using (on purpose)

A. “Is multi-agent justified?” + role clarity

(from core concepts + SKILL)

Using:
	•	We explicitly chose a small set of specialist agents:
	•	Design Agent – understands ticket & proposes approach.
	•	Coding Agent – modifies repo.
	•	Review Agent – evaluates diff & tests.
	•	Notes/Metadata Agent – summarizes run & lessons.
	•	That matches the book’s idea of role-specialized agents instead of one mega-agent, because:
	•	Tasks are decomposable (design → implement → review).
	•	Different “skills” and prompts make sense at each stage.
	•	It keeps reasoning, code-gen, and critique separate and inspectable.

You’re implicitly practicing the SKILL pattern of:

“Start from the workflow humans already follow, then map steps to agents.”

⸻

B. Workflow-based orchestration, not free-for-all

(from orchestration patterns)

Using:
	•	A workflow / pipeline pattern, not chatty autonomous swarms:
	•	Sequential steps: FetchTicket → AnalyzeRepo → Design → Code → Test → Review → PR → Notes.
	•	Simple conditionals:
	•	if tests fail → one more coding attempt.
	•	if review fails → maybe one retry then stop.
	•	You’re not letting agents freely decide who talks next. Instead, a workflow engine controls execution.

This is straight out of the “explicit orchestration / workflow patterns” chapter: easier to debug, reason about, and tune.

⸻

C. Agents as “model + tools + memory + policy”

(from core concepts + building agents)

Using:
	•	Each agent has:
	•	A model interface (ModelClient).
	•	Access to tools / integrations:
	•	Jira client, GitHub client, test runner, patch applier.
	•	A policy defined via prompts and step-level logic (e.g., “only change these files”, “summarize acceptance criteria first”).
	•	For v1 we’re mostly using short-term, in-run memory (context passed through the workflow).

We’re not yet going deep into sophisticated long-term memory, but we are embodying the basic agent pattern.

⸻

D. Model abstraction & tool-calling mindset

(from building agents + SKILL)

Using:
	•	A ModelClient layer so your agents don’t care if they’re calling:
	•	Claude Code today,
	•	Gemini 3 later,
	•	or a mix.
	•	Tools are first-class:
	•	“Run tests”, “apply patch”, “create PR”, “comment on ticket”.
	•	You’re planning to prompt Claude Code to write code that uses those tools – that’s exactly the “agent + tools” picture, even if we start by calling tools from the host code, not via structured tool calls.

This lines up with the book’s recommendation: keep models swappable, tools explicit.

⸻

E. Evaluation, logging, and “trajectory” mindset

(from evaluation & optimization)

Using:
	•	The run log / run metadata concept as a lightweight trajectory:
	•	For each run you’ll store:
	•	ticket, steps taken, outputs, tests, PR URL, errors.
	•	plus a summary via Notes Agent.
	•	A simple evaluation harness:
	•	Run a small set of “known” tickets through the system.
	•	Track success/failure, test pass/fail, manual quality rating.
	•	You’ll inspect this data to:
	•	refine prompts,
	•	adjust workflow steps,
	•	decide where to add complexity (e.g., more retries, more agents).

This is the book’s evaluation-first / trajectory-based debugging in a lightweight, practical form.

⸻

F. UX principles: observability & control

(from UX principles)

Using:
	•	Observability:
	•	Clear logs per step: which agent did what, and when.
	•	Run summaries from the Notes Agent.
	•	Interruptibility / guardrails:
	•	Confirmation before destructive actions:
	•	branch creation, pushing, opening PRs.
	•	A --dry-run mode.
	•	Capability discovery (a bit):
	•	Command help and docs describing: “Given a Jira ticket, this is what the system does.”

We’re not building a fancy GUI yet, but you’re absolutely using the UX principles: show your work, let the human stay in control.

⸻

2. Concepts we’re mostly omitting for now

These are things in the book / SKILL that we’re intentionally not doing in v1 to keep the system simple and shippable in 6 days.

A. Autonomous orchestration patterns (group chats, round-robin, planners)

Omitting (for now):
	•	Group chat among agents in a shared channel with a router choosing the next speaker.
	•	Round-robin refinement loops where agents just take turns endlessly.
	•	A separate Planner Agent that dynamically decomposes the overall task into sub-tasks and dispatches them.

Why:
Your use case maps nicely to a clear, human-like workflow (human dev’s process), so explicit workflows are easier to debug and reason about. We can always layer a planner in later if we discover tickets that need more dynamic decomposition.

⸻

B. Heavy long-term memory / semantic search infra

Mostly omitting for v1:
	•	Vector databases / semantic indexes for large codebases.
	•	Complex RAG setups with hybrid recency + relevance retrieval.
	•	Learned, persistent knowledge bases about repos.

You do have:
	•	Short-term memory: context passed through steps, plus some textual repo summaries.
	•	A simple “notes” store – but not a full-blown semantic memory system.

We can introduce RAG later if:
	•	codebases get large enough that naive context selection hurts,
	•	or you want the agent to “remember” long-term patterns across many runs.

⸻

C. Advanced workflow engine features (DAGs, parallelism, checkpointing)

Omitting / deferring:
	•	Full DAG-based workflow engine with arbitrary branching.
	•	Parallel execution of steps (e.g., design + static analysis + doc lookup in parallel).
	•	Checkpointed workflows that resume mid-run after crashes or restarts.

In v1 we’re doing:
	•	Straightforward sequential workflow with some conditionals.
	•	Probably no need for parallelism; the model call dominates latency anyway.
	•	Checkpointing is overkill for single PR workflows that complete in minutes.

If this project grows, you may refactor the workflow engine to a DAG pattern, but that’s beyond your 6-day learning goal.

⸻

D. Computer-use / UI-control agents

Not using:
	•	Agents that literally control a browser or desktop:
	•	read screenshots / DOM,
	•	click buttons,
	•	navigate GUIs when APIs are missing.

We don’t need that:
	•	Jira + GitHub have APIs.
	•	Code lives in a repo we can manipulate locally.

This keeps the system simpler and avoids a whole class of brittleness.

⸻

E. Heavy-duty evaluation frameworks & LLM-as-a-judge

Keeping it light:
	•	We’re not:
	•	training a big evaluation suite with thousands of tasks,
	•	running LLM judges to rate PR quality,
	•	building sophisticated dashboards.

For your goals, tests + simple metrics + your own judgment are enough.
If you later want to compare models (Claude vs Gemini) or patterns formally, you can add LLM-based scoring.

⸻

F. Full-fledged multi-user / product-grade UX

Deliberately skipping for v1:
	•	Multi-user accounts, permissions, cost dashboards.
	•	Rich web UI with progress bars, timeline visualizations, and agent avatars.
	•	Complex “cost-aware delegation” mechanisms (budgets, per-run caps, etc.).

Instead, you get:
	•	Developer-focused CLI and logs.
	•	A few confirmations/flags to keep you safe.
	•	Docs that explain what’s happening so you can learn.

That matches your stated priority: learning experience first, product polish later.

⸻

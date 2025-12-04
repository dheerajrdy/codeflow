#!/usr/bin/env python3
"""
Comprehensive Multi-Agent System Evaluation

A focused evaluation suite that teaches:
1. When multi-agent teams outperform single agents
2. How tool availability changes the value proposition
3. Which orchestration pattern (RoundRobin vs AI) works better
4. Task complexity thresholds that justify multi-agent overhead

Configurations (4 total):
- Direct Model (baseline)
- Single Agent + Tools
- Multi-Agent (RoundRobin orchestration)
- Multi-Agent (AI orchestration)

Task categories (tight, focused):
- Simple Reasoning (3 tasks) - baseline comparison
- Tool-Heavy (3 tasks) - test tool usage value
- Complex Planning (2 tasks) - test coordination value
- Verification (2 tasks) - test critique value

Usage:
    python comprehensive-evaluation.py         # Full evaluation (10 tasks)
    python comprehensive-evaluation.py quick   # Quick test (3 tasks)

Focus: Generate clear insights about when/why multi-agent systems matter.
"""

import argparse
import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from picoagents import Agent
from picoagents.eval import (
    AgentEvalTarget,
    CompositeJudge,
    EvalRunner,
    FuzzyMatchJudge,
    LLMEvalJudge,
    ModelEvalTarget,
    OrchestratorEvalTarget,
)
from picoagents.llm import AzureOpenAIChatCompletionClient
from picoagents.orchestration import AIOrchestrator, RoundRobinOrchestrator
from picoagents.termination import MaxMessageTermination, TextMentionTermination
from picoagents.tools import (
    CalculatorTool,
    DateTimeTool,
    JSONParserTool,
    RESEARCH_TOOLS_AVAILABLE,
    TaskStatusTool,
    ThinkTool,
)

# Import research tools if available
if RESEARCH_TOOLS_AVAILABLE:
    from picoagents.tools._research_tools import GoogleSearchTool
else:
    GoogleSearchTool = None
from picoagents.types import EvalTask




# ============================================================================
# TASK SUITES
# ============================================================================


def create_quick_tasks() -> List[EvalTask]:
    """Minimal task set for quick testing (one from each category)."""
    return [
        EvalTask(
            name="Math-Simple",
            input="If a train travels 240 miles in 3 hours, what is its average speed?",
            expected_output="80 miles per hour",
        ),
        EvalTask(
            name="Calculator",
            input="Calculate: (12 * 8) + (144 / 12)",
            expected_output="108",
        ),
        EvalTask(
            name="Logic-Puzzle",
            input="Three people have different jobs: doctor, teacher, lawyer. Alice is not a doctor. Bob is not a teacher. Carol is not a lawyer. What is each person's job?",
            expected_output="Two valid complete assignments exist: (1) Alice=teacher, Bob=lawyer, Carol=doctor OR (2) Alice=lawyer, Bob=doctor, Carol=teacher. Providing either or both is acceptable.",
        ),
    ]


def create_mini_tasks() -> Dict[str, List[EvalTask]]:
    """Mini comprehensive test - 1 task from each suite for fast iteration."""
    return {
        "Simple-Reasoning": [create_simple_reasoning_tasks()[0]],  # Just math
        "Tool-Heavy": [create_tool_heavy_tasks()[0]],  # Just one search task
        "Planning": [create_planning_tasks()[0]],  # Just one planning task
        "Verification": [create_verification_tasks()[0]],  # Just one verification task
    }


def create_simple_reasoning_tasks() -> List[EvalTask]:
    """Tasks that test basic reasoning without tools."""
    return [
        EvalTask(
            name="Math Word Problem",
            input="If a train travels 240 miles in 3 hours, and then 180 miles in 2 hours, what is its average speed for the entire journey?",
            expected_output="The average speed is 84 miles per hour (420 total miles divided by 5 total hours).",
        ),
        EvalTask(
            name="Logic Puzzle",
            input="Three people - Alice, Bob, and Carol - have different professions: doctor, lawyer, teacher. Alice is not a doctor. Bob is not a lawyer. Carol is not a teacher. Who has which profession?",
            expected_output="Alice is a lawyer, Bob is a teacher, Carol is a doctor.",
        ),
        EvalTask(
            name="Reading Comprehension",
            input="The Eiffel Tower was completed in 1889 for the World's Fair. It was initially criticized but became Paris's most iconic landmark. How many years ago was it built? (Use 2024 as current year)",
            expected_output="135 years ago (2024 - 1889 = 135)",
        ),
    ]


def create_tool_heavy_tasks() -> List[EvalTask]:
    """Tasks that require tool composition and web research."""
    return [
        EvalTask(
            name="Podcast Research",
            input="""Did Andrej Karpathy have a podcast interview with Dwarkesh Patel
            where he discussed Eureka Labs? If so, what did he say was the primary
            goal of Eureka Labs? Provide specific quotes if possible.""",
            expected_output="""Yes, Andrej Karpathy has discussed Eureka Labs, where he is founder and CEO.
            The primary goal of Eureka Labs is to personalize education using AI teaching assistants.
            According to a Business Insider article, Eureka Labs employs an AI teaching assistant that
            allows students to ask questions and receive a more customized and interactive experience,
            surpassing what is possible with a series of recorded lessons alone. Their first product is
            an AI course titled LLM101n, aimed at teaching students how to develop AI models.""",
        ),
        EvalTask(
            name="Tech Event Research",
            input="""What were the key announcements from OpenAI's most recent DevDay
            conference? Include the date of the event and list at least 3 major
            announcements with brief descriptions.""",
            expected_output="""The most recent OpenAI DevDay conference took place on October 1, 2024,
            in San Francisco. Three major announcements: (1) Realtime API Public Beta for low-latency
            voice applications, (2) Vision Fine-Tuning allowing GPT-4o fine-tuning with images, and
            (3) Model Distillation and Prompt Caching for cost reduction and improved performance.""",
        ),
        EvalTask(
            name="Academic Paper Search",
            input="""Find a recent paper (2024 or 2025) on arXiv about 'multi-agent reinforcement learning'.
            What is the title, authors, and main contribution of one of the top recent results?
            Does the paper mention any publicly available code repository?""",
            expected_output="""Recent 2024 papers include: 'Language Grounded Multi-agent Reinforcement Learning
            with Human-interpretable Communication' by Huao Li et al., which proposes aligning MARL agent
            communication with human natural language using synthetic data from embodied LLMs. Another is
            'Episodic Future Thinking Mechanism for Multi-agent Reinforcement Learning' by Dongsu Lee and
            Minhae Kwon, introducing cognitive science-inspired episodic future thinking in MARL. Neither
            explicitly mentions publicly available code repositories.""",
        ),
    ]


def create_planning_tasks() -> List[EvalTask]:
    """Tasks requiring decomposition and multi-step planning."""
    return [
        EvalTask(
            name="Multi-Constraint Itinerary",
            input="""Plan a 3-day weekend trip to San Francisco for 2 people with these constraints:
            - Budget: $1500 total
            - Must include: Golden Gate Bridge, Alcatraz, one food experience
            - Prefer public transportation
            - Stay in centrally-located hotel
            Provide: day-by-day itinerary, budget breakdown, transportation details.""",
            expected_output="Complete itinerary with timing, costs, and logistics",
        ),
        EvalTask(
            name="Resource Allocation",
            input="""You have 10 hours to prepare for three exams: Math (40% of grade), History (30% of grade), Science (30% of grade).
            Your current scores: Math 70%, History 85%, Science 75%.
            Each hour of study typically improves a score by 3%.
            How should you allocate study time to maximize your overall GPA?""",
            expected_output="Study allocation with reasoning about diminishing returns and maximizing weighted outcome",
        ),
    ]


def create_verification_tasks() -> List[EvalTask]:
    """Tasks where critique/review adds significant value."""
    return [
        EvalTask(
            name="Fact Checking",
            input="""Verify these claims:
            1. "The human brain uses 20% of the body's energy despite being only 2% of body weight"
            2. "Coffee dehydrates you and should not count toward daily water intake"
            3. "Reading in dim light damages your eyesight permanently"

            For each, state if true/false and provide brief explanation.""",
            expected_output="Claim-by-claim analysis: 1=True, 2=False (myth), 3=False (myth), with explanations",
        ),
        EvalTask(
            name="Argument Analysis",
            input="""Analyze this argument for logical fallacies:
            "We should ban all social media because my teenager spends too much time on it.
            Everyone I know agrees that social media is destroying society.
            Before social media, people were happier and more connected."

            Identify fallacies and explain why the argument is weak.""",
            expected_output="Identified fallacies: hasty generalization, anecdotal evidence, appeal to nostalgia, post hoc reasoning",
        ),
    ]


# ============================================================================
# CONFIGURATIONS
# ============================================================================


async def create_all_configurations(client) -> List[tuple]:
    """Create all configurations for focused comparison."""
    configs = []

    # 1. Direct Model (baseline)
    configs.append(
        (
            "Direct-Model",
            ModelEvalTarget(
                client=client,
                name="Direct-Model",
                system_message="You are a helpful, accurate assistant. Provide clear, concise answers.",
            ),
        )
    )

    # 2. Single Agent + Tools
    tools = [
        ThinkTool(),
        CalculatorTool(),
        DateTimeTool(),
        JSONParserTool(),
        TaskStatusTool(),
    ]

    # Add GoogleSearchTool if available
    if RESEARCH_TOOLS_AVAILABLE and GoogleSearchTool:
        google_api_key = os.getenv("GOOGLE_API_KEY")
        google_cse_id = os.getenv("GOOGLE_CSE_ID")
        if google_api_key and google_cse_id:
            tools.append(GoogleSearchTool(api_key=google_api_key, cse_id=google_cse_id))

    agent_with_tools = Agent(
        name="assistant",
        description="A helpful assistant with tool access",
        instructions="""You are a knowledgeable assistant with access to tools.
        Use tools when they would improve accuracy. Think step-by-step for
        complex problems. For research tasks, use google_search to find current information.""",
        model_client=client,
        tools=tools,
    )
    configs.append(("Single-Agent-Tools", AgentEvalTarget(agent_with_tools)))

    # 3. Multi-Agent with RoundRobin Orchestration
    configs.append(await create_roundrobin_team(client))

    # 4. Multi-Agent with AI Orchestration
    configs.append(await create_ai_orchestrated_team(client))

    return configs


def _create_team_agents(client) -> List[Agent]:
    """Create the standard team agents (reused by both orchestrators)."""

    planner = Agent(
        name="planner",
        description="Strategic task planner",
        instructions="""Analyze the task and create a clear plan.
        Break complex problems into steps. Be concise.""",
        model_client=client,
        tools=[ThinkTool()],
    )

    solver = Agent(
        name="solver",
        description="Task executor with tools - gathers information and solves tasks",
        instructions="""Execute the plan using available tools efficiently.

IMPORTANT GUIDELINES:
1. When you find an answer, use TaskStatusTool to mark it COMPLETE
2. Do NOT repeat searches if information is already available in conversation
3. Gather information methodically but avoid redundant tool calls
4. After completing work, end your message with: READY FOR REVIEW
5. Do NOT ask the user for clarification - provide complete answers based on available information
6. If multiple valid solutions exist, provide ALL of them

You are solving tasks autonomously. Present all findings and solutions directly.
Use tools strategically - check conversation history before re-searching.
When done, mark task complete and say READY FOR REVIEW.""",
        model_client=client,
        tools=[
            ThinkTool(),
            CalculatorTool(),
            DateTimeTool(),
            JSONParserTool(),
            TaskStatusTool(),
        ],
    )

    # Add GoogleSearchTool if both tool and credentials available
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")
    if RESEARCH_TOOLS_AVAILABLE and GoogleSearchTool and google_api_key and google_cse_id:
        solver.tools.append(GoogleSearchTool(api_key=google_api_key, cse_id=google_cse_id))

    reviewer = Agent(
        name="reviewer",
        description="Quality assurance specialist - validates solutions and checks for completeness. Schedule me after solver finishes work.",
        instructions="""Verify work is correct and complete. Check if solution:
        1. Answers the original question fully
        2. Considers alternate solutions if applicable
        3. Provides sufficient detail

        IMPORTANT - You must ALWAYS end with one of these signals:

        - If work is complete and high quality: "APPROVED and READY FOR SUMMARY"

        - If minor issues found (like missing alternate solutions or insufficient detail):
          Provide your feedback, then END with: "READY FOR SUMMARY"
          (The summarizer will incorporate your feedback into the final answer)

        - ONLY if major errors require solver to redo work: "NEEDS REVISION"
          (Specify exactly what needs to be fixed)

        Default to "READY FOR SUMMARY" - let the summarizer incorporate feedback rather than blocking progress.""",
        model_client=client,
        tools=[ThinkTool()],
    )

    # NEW: Summary agent to prevent wheel-spinning
    summarizer = Agent(
        name="summarizer",
        description="""⚠️ PRIORITY AGENT: Schedule me when you see 'READY FOR SUMMARY' or 'Task Status: COMPLETE'.
        I am the FINAL step - I synthesize all work and say TERMINATE to end the conversation.
        DO NOT keep selecting other agents after work is done - select me to finish efficiently and provide the final answer.""",
        instructions="""You are the final summarizer. Your role is to:
        1. Review ALL previous work, findings, and feedback in the conversation
        2. Incorporate any reviewer feedback into your synthesis
        3. Synthesize a complete, well-structured final answer
        4. ALWAYS end your response with exactly: TERMINATE

        IMPORTANT: You MUST say TERMINATE at the end of your response to signal completion.
        Do not repeat work already done - just provide the final synthesis incorporating all insights.""",
        model_client=client,
        tools=[ThinkTool()],
    )

    return [planner, solver, reviewer, summarizer]


async def create_roundrobin_team(client) -> tuple:
    """Create team with RoundRobin orchestration (fixed order)."""
    agents = _create_team_agents(client)

    orchestrator = RoundRobinOrchestrator(
        agents=agents,
        termination=MaxMessageTermination(max_messages=30)
        | TextMentionTermination(text="APPROVED")
        | TextMentionTermination(text="TERMINATE")
        | TextMentionTermination(text="Task Status: COMPLETE"),
        max_iterations=15,  # Increased for research tasks
    )

    return ("Multi-Agent-RoundRobin", OrchestratorEvalTarget(orchestrator))


async def create_ai_orchestrated_team(client) -> tuple:
    """Create team with AI orchestration (dynamic speaker selection)."""
    agents = _create_team_agents(client)

    # Note: Orchestration prioritization is encoded in agent descriptions
    # (especially the summarizer's description) since AIOrchestrator uses
    # agent descriptions to decide which agent to select next

    orchestrator = AIOrchestrator(
        agents=agents,
        model_client=client,
        termination=MaxMessageTermination(max_messages=30)
        | TextMentionTermination(text="TERMINATE"),
        # Note: "READY FOR SUMMARY", "READY FOR REVIEW", and "Task Status: COMPLETE" are
        # workflow signals visible to the AI orchestrator but do NOT terminate the conversation.
        # Only TERMINATE actually ends the conversation.
        max_iterations=20,  # Increased to allow full workflow: plan → solve → review → summarize
    )

    return ("Multi-Agent-AI", OrchestratorEvalTarget(orchestrator))


# ============================================================================
# VISUALIZATION
# ============================================================================


def create_visualizations(results_df: pd.DataFrame, output_dir: Path):
    """Generate 2x2 evaluation visualizations with clear storytelling."""
    PRIMARY_COLOR = "#4146DB"
    SECONDARY_COLOR = "#323E50"
    COLORS = [PRIMARY_COLOR, SECONDARY_COLOR, '#7B7FE8', '#4A5568']

    # Configuration name mappings for shorter labels
    CONFIG_SHORT_NAMES = {
        'Direct-Model': 'Direct\nModel',
        'Single-Agent-Tools': 'Single\nAgent',
        'Multi-Agent-RoundRobin': 'Multi-Agent\nRoundRobin',
        'Multi-Agent-AI': 'Multi-Agent\nAI'
    }

    # 3-chart layout: 2 on top, 1 full-width on bottom
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.35, wspace=0.3)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])  # Full width bottom chart
    fig.suptitle("Multi-Agent System Evaluation Results", fontsize=18, fontweight="bold", y=0.98)

    # Aggregate by configuration
    summary = results_df.groupby("configuration").agg({"overall_score": "mean"}).round(2)
    configs = summary.index.tolist()
    scores = summary["overall_score"].tolist()

    # TOP-LEFT: Overall Performance with multiline y-axis labels
    bars1 = ax1.barh(configs, scores, color=PRIMARY_COLOR, alpha=0.8)
    for bar, score in zip(bars1, scores):
        ax1.text(score + 0.15, bar.get_y() + bar.get_height() / 2, f"{score:.1f}/10",
                va="center", fontweight="bold", fontsize=11)
    ax1.set_xlabel("Average Score (0-10)", fontweight="bold", fontsize=12)
    ax1.set_title("Overall Performance", fontweight="bold", pad=15, fontsize=14)
    ax1.set_xlim(0, 10.5)
    ax1.grid(axis="x", alpha=0.3)
    # Use shorter multiline labels for y-axis
    ax1.set_yticklabels([CONFIG_SHORT_NAMES.get(c, c) for c in configs], fontsize=10)

    # Order suites by Direct-Model score (easy = high, hard = low)
    suite_difficulty = results_df[results_df['configuration'] == 'Direct-Model'].groupby('suite')['overall_score'].mean().sort_values(ascending=False)
    ordered_suites = suite_difficulty.index.tolist()

    # TOP-RIGHT: Token Efficiency Per Task (Score per 1000 tokens, only for successful tasks)
    efficiency_data = []
    for suite in ordered_suites:
        suite_data = results_df[results_df['suite'] == suite]
        for config in configs:
            config_data = suite_data[suite_data['configuration'] == config]
            # Only count successful tasks (score >= 7.0)
            successful = config_data[config_data['overall_score'] >= 7.0]
            if len(successful) > 0:
                avg_score = successful['overall_score'].mean()
                avg_tokens = successful['tokens_total'].mean()
                efficiency = (avg_score / (avg_tokens / 1000)) if avg_tokens > 0 else 0
                efficiency_data.append({'suite': suite, 'config': config, 'efficiency': efficiency})

    # Plot as grouped bar chart with value labels
    eff_df = pd.DataFrame(efficiency_data)
    suite_names = ordered_suites
    x_eff = np.arange(len(suite_names))
    width_eff = 0.2

    for i, config in enumerate(configs):
        config_eff = [eff_df[(eff_df['suite'] == suite) & (eff_df['config'] == config)]['efficiency'].values[0]
                     if len(eff_df[(eff_df['suite'] == suite) & (eff_df['config'] == config)]) > 0 else 0
                     for suite in suite_names]
        bars = ax2.bar([xi + i * width_eff for xi in x_eff], config_eff, width_eff,
               label=CONFIG_SHORT_NAMES.get(config, config), color=COLORS[i % len(COLORS)], alpha=0.8)

        # Add value labels on top of bars for better readability
        for j, (bar, val) in enumerate(zip(bars, config_eff)):
            if val > 1:  # Only show labels for visible bars
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        f'{val:.0f}', ha='center', va='bottom', fontsize=8, rotation=0)

    ax2.set_xlabel("Task Category", fontweight="bold", fontsize=12)
    ax2.set_ylabel("Score per 1K Tokens\n(Successful Tasks Only)", fontweight="bold", fontsize=11)
    ax2.set_title("Token Efficiency by Task", fontweight="bold", pad=15, fontsize=14)
    ax2.set_xticks([xi + width_eff * 1.5 for xi in x_eff])
    ax2.set_xticklabels(suite_names, rotation=0, ha='center', fontsize=11)
    ax2.legend(loc='upper right', fontsize=9, framealpha=0.95)
    ax2.grid(axis="y", alpha=0.3)

    # BOTTOM: Full-width individual task performance chart
    # Get all unique tasks across all suites
    task_data = []
    for _, row in results_df.iterrows():
        task_data.append({
            'task': row['task'],
            'suite': row['suite'],
            'config': row['configuration'],
            'score': row['overall_score']
        })

    task_df = pd.DataFrame(task_data)

    # Group tasks by suite and calculate average per config
    task_scores = task_df.groupby(['suite', 'task', 'config'])['score'].mean().reset_index()

    # Get unique tasks per suite (in order)
    suite_tasks = []
    for suite in ordered_suites:
        suite_data = task_scores[task_scores['suite'] == suite]
        tasks = suite_data['task'].unique().tolist()
        suite_tasks.extend([(suite, task) for task in tasks])

    # Create grouped bar chart
    x_pos = np.arange(len(suite_tasks))
    width = 0.2

    for i, config in enumerate(configs):
        config_scores = []
        for suite, task in suite_tasks:
            score_val = task_scores[
                (task_scores['suite'] == suite) &
                (task_scores['task'] == task) &
                (task_scores['config'] == config)
            ]['score']
            config_scores.append(score_val.values[0] if len(score_val) > 0 else 0)

        ax3.bar([x + i * width for x in x_pos], config_scores, width,
               label=CONFIG_SHORT_NAMES.get(config, config), color=COLORS[i % len(COLORS)], alpha=0.8)

    # Format x-axis labels - horizontal and multiline for readability
    task_labels = []
    for suite, task in suite_tasks:
        # Split long task names into multiple lines
        if len(task) > 20:
            words = task.split()
            line1 = ' '.join(words[:len(words)//2])
            line2 = ' '.join(words[len(words)//2:])
            task_labels.append(f"{line1}\n{line2}")
        else:
            task_labels.append(task)

    ax3.set_xticks([x + width * 1.5 for x in x_pos])
    ax3.set_xticklabels(task_labels, rotation=0, ha='center', fontsize=10)
    ax3.set_ylabel("Score (0-10)", fontweight="bold", fontsize=13)
    ax3.set_xlabel("Individual Tasks (Grouped by Category)", fontweight="bold", fontsize=13)
    ax3.set_title("Performance by Individual Task", fontweight="bold", pad=15, fontsize=15)
    # Move legend to lower right with bigger font
    ax3.legend(loc='lower right', fontsize=11, framealpha=0.95, ncol=2)
    ax3.grid(axis="y", alpha=0.3, linestyle='--')
    ax3.set_ylim(0, 10.5)

    # Add subtle vertical lines to separate suites
    current_pos = 0
    for suite in ordered_suites[:-1]:
        suite_count = len([s for s, t in suite_tasks if s == suite])
        current_pos += suite_count
        ax3.axvline(x=current_pos - 0.5, color='gray', linestyle=':', alpha=0.4, linewidth=1)

    plt.tight_layout()
    output_path = output_dir / "evaluation_results.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"\n📊 Visualization saved: {output_path}")


# ============================================================================
# EVALUATION EXECUTION
# ============================================================================


async def run_evaluation_suite(mode: str = "full"):
    """Run comprehensive evaluation across all configurations and tasks."""

    mode_display = {
        "quick": "QUICK TEST",
        "mini": "MINI COMPREHENSIVE TEST",
        "full": "FULL EVALUATION"
    }.get(mode, "FULL EVALUATION")
    print("=" * 70)
    print(f"MULTI-AGENT SYSTEM {mode_display}")
    print("=" * 70)

    # Setup Azure OpenAI
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")

    if not azure_endpoint or not api_key:
        print("❌ Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
        return

    client = AzureOpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        azure_deployment=deployment,
    )

    # Create output directory
    if mode == "quick":
        output_dir = Path(__file__).parent / "quick_results"
    elif mode == "mini":
        output_dir = Path(__file__).parent / "mini_results"
    else:
        output_dir = Path(__file__).parent / "comprehensive_results"
    output_dir.mkdir(exist_ok=True)

    # Create task suites based on mode
    print("\n📋 Creating task suites...")
    if mode == "quick":
        all_tasks = create_quick_tasks()
        task_suites = {"Quick-Test": all_tasks}
    elif mode == "mini":
        task_suites = create_mini_tasks()
    else:
        task_suites = {
            "Simple-Reasoning": create_simple_reasoning_tasks(),
            "Tool-Heavy": create_tool_heavy_tasks(),
            "Planning": create_planning_tasks(),
            "Verification": create_verification_tasks(),
        }

    total_tasks = sum(len(tasks) for tasks in task_suites.values())
    print(f"   Created {len(task_suites)} task categories, {total_tasks} total tasks")

    # Create configurations
    print("\n🤖 Creating agent configurations...")
    configurations = await create_all_configurations(client)
    print(f"   Created {len(configurations)} configurations:")
    for name, _ in configurations:
        print(f"      - {name}")

    # Create judge
    print("\n⚖️  Setting up evaluation judge...")
    judge_client = AzureOpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        azure_deployment=deployment,
    )

    # Use composite judge with custom instructions for fair multi-agent evaluation
    multi_agent_instructions = """
IMPORTANT - Multi-Agent Evaluation Guidelines:

**SCORING PHILOSOPHY**:
- If the answer is CORRECT and COMPLETE, score 8-10 regardless of response length
- If the answer is CORRECT but INCOMPLETE, score 6-7
- If the answer is INCORRECT, score based on partial correctness (0-5)

**DO NOT PENALIZE**:
- Response length or verbosity
- Multi-agent collaborative process visibility (planner → solver → reviewer → summarizer)
- Showing reasoning steps or validation process
- Format variations for equivalent answers

**EVALUATION CRITERIA**:

1. Completeness:
   - Providing multiple valid solutions when they exist = COMPLETE (score 9-10)
   - Providing one valid solution when multiple exist = PARTIALLY COMPLETE (score 6-7)
   - Missing alternate solutions entirely = INCOMPLETE (score 4-5)

2. Helpfulness:
   - Correct answer with clear reasoning = HELPFUL (score 9-10)
   - Correct answer with minimal explanation = MODERATELY HELPFUL (score 7-8)
   - Incorrect or unclear answer = NOT HELPFUL (score 0-6)

3. Clarity:
   - Logically structured with clear reasoning = CLEAR (score 9-10)
   - Understandable but could be better organized = MODERATELY CLEAR (score 7-8)
   - Confusing or contradictory = UNCLEAR (score 0-6)
   - NOTE: Longer responses can be perfectly clear; judge structure, not brevity

**COMMON PITFALLS TO AVOID**:
❌ "This is correct but verbose for a simple task" → Score: 6/10
✅ "This is correct and complete" → Score: 9-10/10

❌ "Shows unnecessary multi-agent process overhead"
✅ "Shows clear reasoning process with validation"

**EXAMPLES**:
- Math problem with correct answer + reasoning → Completeness: 9-10/10
- Logic puzzle with one valid solution (two exist) → Completeness: 6-7/10
- Any task with clear, logical explanation → Clarity: 9-10/10
"""

    llm_judge = LLMEvalJudge(
        client=judge_client,
        name="gpt-4.1-mini-judge",
        default_criteria=["accuracy", "completeness", "helpfulness", "clarity"],
        custom_instructions=multi_agent_instructions,
    )

    # Use LLM judge only - FuzzyMatch penalizes verbose but correct multi-agent responses
    # The LLM judge with custom instructions already evaluates accuracy appropriately
    runner = EvalRunner(judge=llm_judge, parallel=False)

    # Run evaluations
    print("\n🔬 Running evaluations...")
    print("   This may take several minutes...\n")

    all_results = []

    for suite_name, tasks in task_suites.items():
        print(f"\n{'='*70}")
        print(f"Task Suite: {suite_name}")
        print(f"{'='*70}")

        for config_name, config_target in configurations:
            print(f"\n   Testing: {config_name} ({len(tasks)} tasks)")

            try:
                scores = await runner.evaluate(config_target, tasks)

                for task, score in zip(tasks, scores):
                    if score.trajectory and score.trajectory.usage:
                        usage = score.trajectory.usage
                        # Collect reasoning for understanding WHY scores are what they are
                        reasoning_summary = " | ".join(
                            f"{k}: {v[:100]}" for k, v in score.reasoning.items()
                        )

                        result = {
                            "suite": suite_name,
                            "configuration": config_name,
                            "task": task.name,
                            "overall_score": score.overall,
                            "accuracy": score.dimensions.get("accuracy", 0),
                            "completeness": score.dimensions.get("completeness", 0),
                            "helpfulness": score.dimensions.get("helpfulness", 0),
                            "clarity": score.dimensions.get("clarity", 0),
                            "tokens_total": usage.tokens_input + usage.tokens_output,
                            "duration_ms": usage.duration_ms,
                            "llm_calls": usage.llm_calls,
                            "cost": usage.cost_estimate or 0,
                            "success": score.trajectory.success,
                            "reasoning": reasoning_summary,  # WHY the scores are what they are
                            "stop_reason": score.trajectory.metadata.get("stop_reason", "unknown"),
                            "message_count": len(score.trajectory.messages),
                            "iterations": score.trajectory.metadata.get("iterations", 0),
                        }
                        all_results.append(result)

                        # Save full trajectory for detailed analysis
                        # Save for multi-agent runs or low scores (potential issues)
                        if "Multi-Agent" in config_name or score.overall < 7.0:
                            trajectory_dir = output_dir / "trajectories"
                            trajectory_dir.mkdir(exist_ok=True)

                            # Create sanitized filename
                            safe_task_name = task.name.replace(" ", "_").replace("/", "_")
                            trajectory_file = trajectory_dir / f"{suite_name}_{config_name}_{safe_task_name}.json"

                            # Serialize trajectory
                            trajectory_data = {
                                "task": task.model_dump(),
                                "configuration": config_name,
                                "score": score.overall,
                                "dimensions": score.dimensions,
                                "reasoning": score.reasoning,
                                "messages": [
                                    {
                                        "role": msg.role,
                                        "content": msg.content[:1000] if isinstance(msg.content, str) else str(msg.content)[:1000],  # Truncate long content
                                        "name": msg.name if hasattr(msg, 'name') else None,
                                    }
                                    for msg in score.trajectory.messages
                                ],
                                "usage": usage.model_dump() if usage else None,
                                "metadata": score.trajectory.metadata,
                                "stop_reason": score.trajectory.metadata.get("stop_reason", "unknown"),
                                # Add selection history if available (AI orchestrator)
                                "selection_history": score.trajectory.metadata.get("selection_history", []),
                            }

                            import json
                            with open(trajectory_file, 'w') as f:
                                json.dump(trajectory_data, f, indent=2)

                        # Quick feedback
                        avg_score = score.overall
                        print(f"      {task.name}: {avg_score:.1f}/10")

            except Exception as e:
                print(f"      ❌ Error: {str(e)}")
                continue

    # Save results
    results_df = pd.DataFrame(all_results)
    results_filename = "quick_results.csv" if mode == "quick" else "comprehensive_results.csv"
    results_df.to_csv(output_dir / results_filename, index=False)

    # Generate visualizations
    create_visualizations(results_df, output_dir)

    # Generate summary statistics
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    # Overall performance by configuration
    print("\n📊 Overall Performance by Configuration:")
    config_summary = (
        results_df.groupby("configuration")
        .agg(
            {
                "overall_score": ["mean", "std"],
                "tokens_total": "mean",
                "duration_ms": "mean",
                "llm_calls": "mean",
            }
        )
        .round(2)
    )
    print(config_summary.to_string())

    # Performance by task suite
    print("\n📊 Performance by Task Suite:")
    suite_summary = (
        results_df.groupby(["suite", "configuration"])["overall_score"]
        .mean()
        .round(2)
        .unstack()
    )
    print(suite_summary.to_string())

    # Efficiency metrics
    print("\n💰 Efficiency Metrics (Score per 1000 tokens):")
    efficiency = results_df.groupby("configuration").apply(
        lambda x: (x["overall_score"].mean() / (x["tokens_total"].mean() / 1000))
    ).round(2)
    print(efficiency.to_string())

    # Best configuration per suite
    print("\n🏆 Best Configuration per Task Suite:")
    best_per_suite = (
        results_df.groupby(["suite", "configuration"])["overall_score"]
        .mean()
        .reset_index()
        .sort_values("overall_score", ascending=False)
        .drop_duplicates(subset=["suite"])
    )
    for _, row in best_per_suite.iterrows():
        print(
            f"   {row['suite']}: {row['configuration']} ({row['overall_score']:.1f}/10)"
        )

    print("\n✅ Evaluation complete!")
    print(f"   Results saved to: {output_dir}")
    print(f"   - comprehensive_results.csv")

    return results_df, output_dir


# ============================================================================
# MAIN
# ============================================================================


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent System Evaluation Suite"
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="full",
        choices=["quick", "mini", "full"],
        help="Evaluation mode: 'quick' (3 tasks, ~30s), 'mini' (4 tasks from all suites, ~1min), or 'full' (10 tasks, ~5-10min)",
    )

    args = parser.parse_args()

    results_df, output_dir = await run_evaluation_suite(mode=args.mode)

    # Additional analysis recommendations
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)

    if args.mode == "quick":
        print("""
1. Review quick_results.csv for detailed scores + reasoning
2. Check evaluation_results.png for performance vs efficiency
3. Look for patterns in the reasoning column - WHY are scores what they are?
4. Tune parameters if needed:
   - Adjust max_iterations, max_messages in team configs
   - Refine agent instructions based on reasoning feedback
5. Run full evaluation when ready: python comprehensive-evaluation.py full
        """)
    else:
        print("""
1. Review comprehensive_results.csv for detailed scores + reasoning
2. Check evaluation_results.png for visualizations
3. Analyze patterns:
   - Which configurations excel at which task types?
   - Where does multi-agent overhead not pay off?
   - Read reasoning column to understand WHY scores differ
4. Update evaluation chapter with insights and charts
        """)


if __name__ == "__main__":
    asyncio.run(main())

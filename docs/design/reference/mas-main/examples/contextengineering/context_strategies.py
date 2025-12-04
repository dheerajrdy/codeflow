#!/usr/bin/env python3
"""
Context Engineering: Three Strategies for Managing LLM Context Growth

Demonstrates baseline, compaction, and isolation strategies in a single file.
Run with: python context_strategies.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "picoagents"))

import matplotlib.pyplot as plt
from picoagents import Agent
from picoagents._middleware import BaseMiddleware, MiddlewareContext
from picoagents.llm import AzureOpenAIChatCompletionClient
from picoagents.messages import Message
from picoagents.tools import FunctionTool

from mock_tools import (
    analyze_tool,
    company_details_tool,
    funding_info_tool,
    report_tool,
    search_companies_tool,
    traction_metrics_tool,
)
from token_tracking import TokenTrackingMiddleware


# =============================================================================
# MIDDLEWARE: Context Compaction
# =============================================================================


class ContextCompactionMiddleware(BaseMiddleware):
    """Automatically trims old messages, keeps recent turns + system messages."""

    def __init__(self, keep_last_turns: int = 5):
        super().__init__()
        self.keep_last_turns = keep_last_turns

    async def process_request(self, context: MiddlewareContext) -> AsyncGenerator[Any, None]:
        if context.operation == "model_call" and isinstance(context.data, list):
            context.data = self._compact_messages(context.data)
        yield context

    def _compact_messages(self, messages: List[Message]) -> List[Message]:
        if len(messages) <= (self.keep_last_turns * 2 + 2):
            return messages
        system_messages = [m for m in messages if m.role == "system"]
        conversation = [m for m in messages if m.role != "system"]
        recent_conversation = conversation[-(self.keep_last_turns * 2) :]
        return system_messages + recent_conversation

    async def process_response(self, context: MiddlewareContext, result: Any) -> AsyncGenerator[Any, None]:
        yield result

    async def process_error(self, context: MiddlewareContext, error: Exception) -> AsyncGenerator[Any, None]:
        if False:
            yield
        raise error


# =============================================================================
# STRATEGY 1: Baseline (No Context Management)
# =============================================================================


async def run_baseline() -> TokenTrackingMiddleware:
    """Run baseline strategy with no context management."""
    print("\n[1/3] BASELINE: No context management")

    token_tracker = TokenTrackingMiddleware()

    researcher = Agent(
        name="researcher",
        description="Research AI/ML companies without context management",
        instructions="Research companies thoroughly. For each company, gather: details, funding, metrics.",
        model_client=AzureOpenAIChatCompletionClient(
            model="gpt-4.1-mini",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        ),
        max_iterations=30,
        tools=[
            search_companies_tool,
            company_details_tool,
            funding_info_tool,
            traction_metrics_tool,
            analyze_tool,
            report_tool,
        ],
        middlewares=[token_tracker],
    )

    task = """
Research AI/ML companies with these steps:
1. Find companies with search_companies_tool
2. For first 3 companies: get details, funding, and metrics
3. Analyze data with analyze_tool
4. Generate report with report_tool
"""

    await researcher.run(task)
    return token_tracker


# =============================================================================
# STRATEGY 2: Context Compaction
# =============================================================================


async def run_compaction() -> TokenTrackingMiddleware:
    """Run compaction strategy with automatic message trimming."""
    print("\n[2/3] COMPACTION: Automatic message trimming")

    token_tracker = TokenTrackingMiddleware()
    compaction = ContextCompactionMiddleware(keep_last_turns=5)

    researcher = Agent(
        name="researcher",
        description="Research AI/ML companies with context compaction",
        instructions="Research companies thoroughly. For each company, gather: details, funding, metrics.",
        model_client=AzureOpenAIChatCompletionClient(
            model="gpt-4.1-mini",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        ),
        max_iterations=30,
        tools=[
            search_companies_tool,
            company_details_tool,
            funding_info_tool,
            traction_metrics_tool,
            analyze_tool,
            report_tool,
        ],
        middlewares=[compaction, token_tracker],
    )

    task = """
Research AI/ML companies with these steps:
1. Find companies with search_companies_tool
2. For first 3 companies: get details, funding, and metrics
3. Analyze data with analyze_tool
4. Generate report with report_tool
"""

    await researcher.run(task)
    return token_tracker


# =============================================================================
# STRATEGY 3: Context Isolation
# =============================================================================


async def run_isolation() -> TokenTrackingMiddleware:
    """Run isolation strategy with hierarchical agents."""
    print("\n[3/3] ISOLATION: Hierarchical agents with isolated contexts")

    # Specialist agent (isolated context)
    specialist_tracker = TokenTrackingMiddleware()
    specialist = Agent(
        name="specialist",
        description="Research specialist with isolated context",
        instructions="Execute research tasks and return findings.",
        model_client=AzureOpenAIChatCompletionClient(
            model="gpt-4.1-mini",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        ),
        max_iterations=15,
        tools=[
            search_companies_tool,
            company_details_tool,
            funding_info_tool,
            traction_metrics_tool,
            analyze_tool,
        ],
        middlewares=[specialist_tracker],
    )

    # Wrap specialist as tool
    async def research_companies_tool(query: str) -> str:
        response = await specialist.run(query)
        return response.messages[-1].content if response.messages else "No results"

    research_tool = FunctionTool(research_companies_tool)

    # Coordinator agent (separate context)
    coordinator_tracker = TokenTrackingMiddleware()
    coordinator = Agent(
        name="coordinator",
        description="Research coordinator with isolated context",
        instructions="Coordinate research using specialist agent. Synthesize findings into report.",
        model_client=AzureOpenAIChatCompletionClient(
            model="gpt-4.1-mini",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        ),
        max_iterations=5,
        tools=[research_tool, report_tool],
        middlewares=[coordinator_tracker],
    )

    task = """
Research AI/ML companies:
1. Use research_companies_tool to gather company information
2. Generate final report with report_tool
"""

    await coordinator.run(task)

    # Combine token counts from both agents
    combined_tracker = TokenTrackingMiddleware()
    combined_tracker.cumulative_input = (
        specialist_tracker.cumulative_input + coordinator_tracker.cumulative_input
    )
    combined_tracker.cumulative_output = (
        specialist_tracker.cumulative_output + coordinator_tracker.cumulative_output
    )
    combined_tracker.token_history = coordinator_tracker.token_history
    combined_tracker.operation_count = coordinator_tracker.operation_count

    return combined_tracker


# =============================================================================
# VISUALIZATION
# =============================================================================


def generate_visualization(results: Dict[str, Any], output_path: Path):
    """Generate side-by-side comparison chart."""

    PRIMARY_COLOR = "#4146DB"
    SECONDARY_COLOR = "#323E50"
    GREEN_COLOR = "#10B981"

    colors = {
        "baseline": SECONDARY_COLOR,
        "compaction": GREEN_COLOR,
        "isolation": PRIMARY_COLOR,
    }

    strategy_labels = {
        "baseline": "Baseline\n(No Context\nEngineering)",
        "compaction": "Context\nCompaction",
        "isolation": "Context\nIsolation",
    }

    plt.style.use("default")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # LEFT: Total Token Usage
    strategies = []
    totals = []
    strategy_colors = []

    for key, data in results.items():
        strategies.append(strategy_labels[key])
        totals.append(data["summary"]["cumulative_total_tokens"])
        strategy_colors.append(colors[key])

    bars = ax1.barh(
        strategies,
        totals,
        color=strategy_colors,
        alpha=0.85,
        edgecolor=SECONDARY_COLOR,
        linewidth=2,
    )

    for bar, total in zip(bars, totals):
        width = bar.get_width()
        ax1.text(
            width + max(totals) * 0.02,
            bar.get_y() + bar.get_height() / 2.0,
            f"{int(total):,}",
            ha="left",
            va="center",
            fontsize=20,
            fontweight="bold",
            color=SECONDARY_COLOR,
        )

    ax1.set_xlabel("Total Tokens", fontsize=20, fontweight="bold", color=SECONDARY_COLOR)
    ax1.set_title("Total Token Usage", fontsize=22, fontweight="bold", color=SECONDARY_COLOR, pad=20)
    ax1.tick_params(axis="both", which="major", labelsize=17, colors=SECONDARY_COLOR)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_color(SECONDARY_COLOR)
    ax1.spines["bottom"].set_color(SECONDARY_COLOR)
    ax1.grid(axis="x", alpha=0.2, linestyle="--")

    # RIGHT: Token Growth Over Time
    for key, data in results.items():
        history = data["history"]
        model_calls = [h for h in history if h["operation_type"] == "model_call"]

        if model_calls:
            steps = [h["operation"] for h in model_calls]
            cumulative = [h["cumulative_total"] for h in model_calls]
            ax2.plot(
                steps,
                cumulative,
                marker="o",
                linewidth=3,
                color=colors[key],
                label=data["name"],
                markersize=8,
                alpha=0.9,
            )

            final_tokens = cumulative[-1]
            ax2.text(
                steps[-1] + 0.3,
                final_tokens,
                f"{int(final_tokens/1000)}K",
                fontsize=22,
                fontweight="bold",
                color=colors[key],
                va="center",
            )

    ax2.set_xlabel("Model Calls", fontsize=20, fontweight="bold", color=SECONDARY_COLOR)
    ax2.set_ylabel("Cumulative Tokens", fontsize=20, fontweight="bold", color=SECONDARY_COLOR)
    ax2.set_title("Token Growth Over Time", fontsize=22, fontweight="bold", color=SECONDARY_COLOR, pad=20)
    ax2.legend(fontsize=15, loc="upper left", frameon=True, fancybox=True, shadow=False)
    ax2.tick_params(axis="both", which="major", labelsize=17, colors=SECONDARY_COLOR)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.spines["left"].set_color(SECONDARY_COLOR)
    ax2.spines["bottom"].set_color(SECONDARY_COLOR)
    ax2.grid(True, alpha=0.2, linestyle="--")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()


# =============================================================================
# MAIN
# =============================================================================


async def main():
    """Run all three strategies and compare results."""

    print("\n" + "=" * 80)
    print("CONTEXT ENGINEERING: Comparing Three Strategies")
    print("=" * 80)

    # Run all strategies
    baseline_tracker = await run_baseline()
    compaction_tracker = await run_compaction()
    isolation_tracker = await run_isolation()

    # Collect results
    results = {
        "baseline": {
            "name": "Baseline (No Management)",
            "summary": baseline_tracker.get_summary(),
            "history": baseline_tracker.get_history(),
        },
        "compaction": {
            "name": "Context Compaction",
            "summary": compaction_tracker.get_summary(),
            "history": compaction_tracker.get_history(),
        },
        "isolation": {
            "name": "Context Isolation",
            "summary": isolation_tracker.get_summary(),
            "history": isolation_tracker.get_history(),
        },
    }

    # Save results
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)

    data_file = results_dir / "comparison_data.json"
    with open(data_file, "w") as f:
        json.dump(results, f, indent=2)

    # Generate visualization
    print("\n" + "=" * 80)
    print("GENERATING VISUALIZATION")
    print("=" * 80)
    viz_file = results_dir / "context_comparison.png"
    generate_visualization(results, viz_file)
    print(f"\n✓ Visualization saved: {viz_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    baseline_total = baseline_tracker.get_summary()["cumulative_total_tokens"]
    compaction_total = compaction_tracker.get_summary()["cumulative_total_tokens"]
    isolation_total = isolation_tracker.get_summary()["cumulative_total_tokens"]

    compaction_reduction = ((baseline_total - compaction_total) / baseline_total) * 100
    isolation_reduction = ((baseline_total - isolation_total) / baseline_total) * 100

    print(f"\n{'Strategy':<30} {'Total Tokens':>15} {'Reduction':>12}")
    print("-" * 60)
    print(f"{'Baseline':<30} {baseline_total:>15,} {'—':>12}")
    print(f"{'Context Compaction':<30} {compaction_total:>15,} {f'-{compaction_reduction:.1f}%':>12}")
    print(f"{'Context Isolation':<30} {isolation_total:>15,} {f'-{isolation_reduction:.1f}%':>12}")
    print()
    print(f"Best Strategy: Context Isolation ({isolation_reduction:.1f}% reduction)")
    print()


if __name__ == "__main__":
    asyncio.run(main())

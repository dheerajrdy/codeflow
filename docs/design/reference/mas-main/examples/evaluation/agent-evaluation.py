#!/usr/bin/env python3
"""
Comprehensive evaluation comparing direct models, agents, and multi-agent systems. 
"""

import asyncio
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from picoagents import Agent
from picoagents.eval import (
    AgentEvalTarget,
    EvalRunner,
    LLMEvalJudge,
    ModelEvalTarget,
    OrchestratorEvalTarget,
)
from picoagents.llm import AzureOpenAIChatCompletionClient
from picoagents.orchestration import RoundRobinOrchestrator
from picoagents.termination import MaxMessageTermination, TextMentionTermination
from picoagents.types import EvalTask


def create_tasks():
    """Create writing-focused evaluation tasks."""
    return [
        EvalTask(
            name="Report",
            input="Write a report on the origins of artificial intelligence and its early development.",
            expected_output="Well-structured historical report",
        ),
        EvalTask(
            name="Research",
            input="Research and write a brief analysis of renewable energy trends in 2024.",
            expected_output="Well-researched analysis",
        ),
        EvalTask(
            name="Reasoning",
            input="How long would it take Eliud Kipchoge to run across the earth 10 times?",
            expected_output="If Eliud Kipchoge could maintain his marathon world record pace nonstop without rest, it would take him about 19,200 hours ≈ 800 days ≈ 2.2 years to run around the Earth 10 times.",
        ),
    ]


async def create_configurations(client):
    """Create the three system configurations to compare."""

    # 1. Direct Model
    model_target = ModelEvalTarget(
        client=client,
        name="Direct-Model",
        system_message="You are a helpful assistant. Give clear, accurate responses.",
    )

    # 2. Single Agent
    agent = Agent(
        name="assistant",
        description="A helpful assistant for various tasks",
        instructions="You are a knowledgeable assistant. Provide accurate, helpful responses with clear explanations.",
        model_client=client,
    )
    agent_target = AgentEvalTarget(agent, name="Single-Agent")

    # 3. Multi-Agent System (Writer + Critic)

    critic = Agent(
        name="critic",
        description="Critical reviewer who provides constructive feedback",
        instructions="""You are a critical reviewer of tasks and must explore opportunities for improvement. Your goal is to evaluate work that has been done and provide constructive feedback to help   improve the response. If the task is already polished and complete, simply respond with 'APPROVED'.

Be constructive and specific in your feedback to help the   create the best possible final product. Dont be unreasonably critical.""",
        model_client=client,
    )

    orchestrator = RoundRobinOrchestrator(
        agents=[agent, critic],
        termination=MaxMessageTermination(max_messages=10)
        | TextMentionTermination(text="APPROVED"),
        max_iterations=7,
    )

    multiagent_target = OrchestratorEvalTarget(
        orchestrator, name="Multi-Agent-Writer-Critic"
    )

    return [model_target, agent_target, multiagent_target]


def create_visualizations(results_df, output_dir):
    """Create clean, compelling two-panel visualization."""
    plt.style.use("default")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle(
        "Agent System Evaluation: Performance vs Resource Investment",
        fontsize=16,
        fontweight="bold",
        y=0.98,
    )

    # Aggregate metrics by system
    metrics = (
        results_df.groupby("system")
        .agg(
            {
                "overall_score": "mean",
                "accuracy": "mean",
                "helpfulness": "mean",
                "clarity": "mean",
                "tokens_total": "mean",
                "duration_ms": "mean",
            }
        )
        .round(2)
    )

    # Clean system names for display
    system_names = {
        "Direct-Model": "Direct\nModel",
        "Single-Agent": "Single\nAgent",
        "Multi-Agent-Writer-Critic": "Multi-Agent\nSystem",
    }

    # Panel 1: Performance Comparison (Grouped Bar Chart)
    x_pos = range(len(metrics))
    width = 0.2

    performance_metrics = ["overall_score", "accuracy", "helpfulness", "clarity"]
    colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12"]
    labels = ["Overall Score", "Accuracy", "Helpfulness", "Clarity"]

    for i, (metric, color, label) in enumerate(
        zip(performance_metrics, colors, labels)
    ):
        values = [metrics.loc[sys, metric] for sys in metrics.index]
        ax1.bar(
            [x + i * width for x in x_pos],
            values,
            width,
            label=label,
            color=color,
            alpha=0.8,
        )

    ax1.set_xlabel("System Type", fontweight="bold")
    ax1.set_ylabel("Score (0-10)", fontweight="bold")
    ax1.set_title("Performance Quality Metrics", fontweight="bold", pad=20)
    ax1.set_xticks([x + width * 1.5 for x in x_pos])
    ax1.set_xticklabels([system_names[sys] for sys in metrics.index])
    ax1.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    ax1.set_ylim(0, 10)
    ax1.grid(axis="y", alpha=0.3)

    # Panel 2: Resource Investment (Clean Bar Chart with Annotations)
    systems = [system_names[sys] for sys in metrics.index]
    tokens = [metrics.loc[sys, "tokens_total"] for sys in metrics.index]
    scores = [metrics.loc[sys, "overall_score"] for sys in metrics.index]

    # Create bars with different colors
    bars = ax2.bar(systems, tokens, color=["#3498db", "#2ecc71", "#e74c3c"], alpha=0.7)

    # Add score annotations on top of bars
    for i, (bar, score) in enumerate(zip(bars, scores)):
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + max(tokens) * 0.02,
            f"Score: {score:.1f}",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

        # Add efficiency metric below
        efficiency = score / (height / 1000)
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height / 2,
            f"{efficiency:.1f}\npts/1K tokens",
            ha="center",
            va="center",
            fontsize=10,
            color="white",
            fontweight="bold",
        )

    ax2.set_xlabel("System Type", fontweight="bold")
    ax2.set_ylabel("Average Token Usage", fontweight="bold")
    ax2.set_title("Resource Investment & Efficiency", fontweight="bold", pad=20)
    ax2.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "evaluation_results.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Summary statistics with averages
    summary = (
        results_df.groupby("system")
        .agg(
            {
                "overall_score": ["mean", "std"],
                "tokens_total": ["mean", "std"],
                "duration_ms": ["mean", "std"],
                "cost": ["mean", "std"] if "cost" in results_df.columns else ["mean"],
            }
        )
        .round(3)
    )

    return summary


async def main():
    """Run comprehensive evaluation comparing system configurations."""
    print("=, Multi-Agent System Evaluation")
    print("=" * 50)

    # Setup Azure OpenAI
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")

    if not azure_endpoint or not api_key:
        print(
            "❌ Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables"
        )
        return

    client = AzureOpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        azure_deployment=deployment,
    )
    output_dir = Path(__file__).parent

    # Create evaluation components
    tasks = create_tasks()
    configurations = await create_configurations(client)

    judge_client = AzureOpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        azure_deployment=deployment,
    )
    judge = LLMEvalJudge(
        judge_client,
        name="gpt-4.1-mini-judge",
        default_criteria=["accuracy", "helpfulness", "clarity"],
    )
    runner = EvalRunner(judge=judge, parallel=False)  # Sequential for stability

    print(f"Evaluating {len(configurations)} systems on {len(tasks)} tasks")

    # Run evaluations
    all_results = []
    for i, config in enumerate(configurations):
        print(f"\nEvaluating {config.name} ({i+1}/{len(configurations)})")

        scores = await runner.evaluate(config, tasks)

        for task, score in zip(tasks, scores):
            if score.trajectory and score.trajectory.usage:
                usage = score.trajectory.usage
                result = {
                    "system": config.name,
                    "task": task.name,
                    "overall_score": score.overall,
                    "accuracy": score.dimensions.get("accuracy", 0),
                    "helpfulness": score.dimensions.get("helpfulness", 0),
                    "clarity": score.dimensions.get("clarity", 0),
                    "tokens_total": usage.tokens_input + usage.tokens_output,
                    "duration_ms": usage.duration_ms,
                    "llm_calls": usage.llm_calls,
                    "cost": usage.cost_estimate or 0,
                }
                all_results.append(result)

    # Analysis
    results_df = pd.DataFrame(all_results)

    print(f"\n=RESULTS SUMMARY")
    print("=" * 50)

    system_avg = results_df.groupby("system")["overall_score"].mean().round(1)
    for system, avg_score in system_avg.items():
        print(f"{system:20} Average Score: {avg_score}/10")

    # Best system
    best_system = system_avg.idxmax()
    print(f"\n<Best Overall: {best_system} ({system_avg[best_system]}/10)")

    # Task-specific analysis
    print(f"\n=Task-Specific Performance:")
    task_performance = results_df.pivot(
        index="task", columns="system", values="overall_score"
    ).round(1)
    print(task_performance.to_string())

    # Efficiency metrics
    print(f"\nEfficiency Metrics:")
    efficiency_df = (
        results_df.groupby("system")
        .agg({"tokens_total": "mean", "duration_ms": "mean", "cost": "mean"})
        .round(3)
    )
    print(efficiency_df.to_string())

    # Create visualizations
    summary = create_visualizations(results_df, output_dir)

    # Save detailed results
    results_df.to_csv(output_dir / "evaluation_results.csv", index=False)

    print(f"\n Evaluation completed!")
    print(f"=Results saved to: {output_dir}")
    print(f"   - evaluation_results.png (charts)")
    print(f"   - evaluation_results.csv (raw data)")


if __name__ == "__main__":
    asyncio.run(main())

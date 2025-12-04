#!/usr/bin/env python3
"""
Reference-Based Evaluation Demo

Showcases the new reference-based evaluation judges and answer extraction strategies.
Compares:
1. ExactMatchJudge vs FuzzyMatchJudge vs ContainsJudge
2. Different answer extraction strategies
3. CompositeJudge combining multiple evaluation approaches
"""

import asyncio
import os
from pathlib import Path

from picoagents import Agent
from picoagents.eval import (
    AgentEvalTarget,
    CompositeJudge,
    ContainsJudge,
    EvalRunner,
    ExactMatchJudge,
    FuzzyMatchJudge,
    LLMEvalJudge,
)
from picoagents.llm import AzureOpenAIChatCompletionClient
from picoagents.types import EvalTask


def create_test_tasks():
    """Create tasks that highlight different evaluation scenarios."""
    return [
        # Exact match tasks (math, factual)
        EvalTask(name="Math Simple", input="What is 7 * 8?", expected_output="56"),
        EvalTask(
            name="Capital",
            input="What is the capital of Japan?",
            expected_output="Tokyo",
        ),
        # Fuzzy match tasks (similar but not exact)
        EvalTask(
            name="Description",
            input="Describe the Eiffel Tower briefly",
            expected_output="The Eiffel Tower is a famous iron structure in Paris, France",
        ),
        # Contains tasks (answer is part of larger response)
        EvalTask(
            name="Scientific Fact",
            input="What is the chemical symbol for water?",
            expected_output="H2O",
        ),
        # Multi-turn style tasks (would benefit from all_assistant extraction)
        EvalTask(
            name="Complex Explanation",
            input="Explain photosynthesis in simple terms",
            expected_output="Plants use sunlight to make food. They take in carbon dioxide and water. They produce glucose and oxygen.",
        ),
    ]


async def demonstrate_extraction_strategies():
    """Show how different answer extraction strategies work."""
    print("\n" + "=" * 60)
    print("ANSWER EXTRACTION STRATEGIES DEMO")
    print("=" * 60)

    # Create a mock trajectory with multiple messages
    from picoagents.messages import AssistantMessage, ToolMessage, UserMessage
    from picoagents.types import EvalTrajectory, Usage

    task = EvalTask(
        name="Multi-message Task", input="Question", expected_output="Final Answer"
    )

    trajectory = EvalTrajectory(
        task=task,
        messages=[
            UserMessage(content="Question", source="user"),
            AssistantMessage(content="Let me think about this...", source="agent"),
            AssistantMessage(
                content="Actually, the answer is: Final Answer", source="agent"
            ),
            ToolMessage(
                content="Tool executed successfully",
                source="tool",
                tool_call_id="123",
                tool_name="test_tool",
                success=True,
                error=None,
            ),
        ],
        success=True,
        error=None,
        usage=Usage(duration_ms=100, llm_calls=1, tokens_input=50, tokens_output=75),
        metadata={},
    )

    strategies = [
        ("last_non_empty", "Uses last message with content"),
        ("last_assistant", "Uses last AssistantMessage (skips tool results)"),
        ("all_assistant", "Concatenates all AssistantMessages"),
        ("last_content", "Just uses last message content"),
    ]

    for strategy, description in strategies:
        judge = ExactMatchJudge(answer_strategy=strategy)
        extracted = judge.extract_answer(trajectory)

        print(f"\n{strategy:15} | {description}")
        print(f"{'':15} | Extracted: '{extracted}'")
        print(f"{'':15} | Match: {extracted.lower() == 'final answer'}")


async def compare_judge_types():
    """Compare different judge types on the same tasks."""
    print("\n" + "=" * 60)
    print("JUDGE TYPE COMPARISON")
    print("=" * 60)

    # Setup Azure OpenAI
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")

    if not azure_endpoint or not api_key:
        print("❌ Skipping judge comparison - Azure OpenAI credentials not found")
        return

    client = AzureOpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        azure_deployment=deployment,
    )

    # Create agent
    agent = Agent(
        name="test-agent",
        description="A helpful test agent",
        instructions="Provide accurate, helpful answers to questions.",
        model_client=client,
    )
    target = AgentEvalTarget(agent)

    # Create judges
    judges = [
        ("ExactMatch", ExactMatchJudge()),
        ("FuzzyMatch", FuzzyMatchJudge(threshold=0.7)),
        ("Contains", ContainsJudge()),
        (
            "Composite",
            CompositeJudge(
                [(ExactMatchJudge(), 0.4), (FuzzyMatchJudge(threshold=0.7), 0.6)]
            ),
        ),
    ]

    # Test on a subset of tasks
    tasks = create_test_tasks()[:3]  # Just first 3 for demo

    print(f"Testing {len(tasks)} tasks with {len(judges)} judge types:")
    print(f"Tasks: {', '.join(t.name for t in tasks)}\n")

    results = {}

    for judge_name, judge in judges:
        print(f"Running {judge_name} judge...")
        runner = EvalRunner(judge, parallel=False)
        scores = await runner.evaluate(target, tasks)
        results[judge_name] = scores

        avg_score = sum(s.overall for s in scores) / len(scores)
        print(f"  Average score: {avg_score:.1f}/10")

    # Show detailed comparison
    print(
        f"\n{'Task':<20} | {'Exact':<8} | {'Fuzzy':<8} | {'Contains':<8} | {'Composite':<8}"
    )
    print("-" * 70)

    for i, task in enumerate(tasks):
        scores_line = f"{task.name:<20} |"
        for judge_name, _ in judges:
            score = results[judge_name][i].overall
            scores_line += f" {score:6.1f}  |"
        print(scores_line)


async def demonstrate_composite_judge():
    """Show the power of composite judges."""
    print("\n" + "=" * 60)
    print("COMPOSITE JUDGE DEMONSTRATION")
    print("=" * 60)

    print("Scenario: Evaluating a code question where we want:")
    print("- 70% weight on correctness (exact match)")
    print("- 30% weight on explanation quality (LLM judge)")

    # Setup would require Azure OpenAI, but we'll simulate
    exact_judge = ExactMatchJudge()
    fuzzy_judge = FuzzyMatchJudge(threshold=0.8)

    composite = CompositeJudge(
        [
            (exact_judge, 0.7),  # 70% on correctness
            (fuzzy_judge, 0.3),  # 30% on similarity
        ],
        name="Code-Evaluation-Judge",
    )

    # Simulate a code task
    task = EvalTask(
        name="Code Function",
        input="Write a function that returns the sum of two numbers",
        expected_output="def add(a, b): return a + b",
    )

    # Simulate different responses
    test_cases = [
        ("Perfect match", "def add(a, b): return a + b"),
        ("Different but correct", "def add(x, y): return x + y"),
        ("Close but wrong", "def subtract(a, b): return a - b"),
        ("Completely wrong", "print('hello world')"),
    ]

    print(f"\nEvaluating different responses:")
    print(f"{'Response':<20} | {'Exact':<8} | {'Fuzzy':<8} | {'Composite':<10}")
    print("-" * 55)

    from picoagents.messages import AssistantMessage, UserMessage
    from picoagents.types import EvalTrajectory, Usage

    for desc, response in test_cases:
        trajectory = EvalTrajectory(
            task=task,
            messages=[
                UserMessage(content=task.input, source="user"),
                AssistantMessage(content=response, source="agent"),
            ],
            success=True,
            error=None,
            usage=Usage(
                duration_ms=100, llm_calls=1, tokens_input=50, tokens_output=25
            ),
            metadata={},
        )

        exact_score = await exact_judge.score(trajectory)
        fuzzy_score = await fuzzy_judge.score(trajectory)
        composite_score = await composite.score(trajectory)

        print(
            f"{desc:<20} | {exact_score.overall:6.1f}  | {fuzzy_score.overall:6.1f}  | {composite_score.overall:8.1f}"
        )


async def show_answer_extraction_benefits():
    """Demonstrate why answer extraction matters."""
    print("\n" + "=" * 60)
    print("WHY ANSWER EXTRACTION MATTERS")
    print("=" * 60)

    print("Problem: Agent gives correct answer but adds extra content")
    print("Without smart extraction: Evaluation fails")
    print("With smart extraction: Evaluation succeeds")

    task = EvalTask(
        name="Capital Question",
        input="What is the capital of France?",
        expected_output="Paris",
    )

    # Simulate agent giving correct answer with extra content
    from picoagents.messages import AssistantMessage, UserMessage
    from picoagents.types import EvalTrajectory, Usage

    trajectory = EvalTrajectory(
        task=task,
        messages=[
            UserMessage(content="What is the capital of France?", source="user"),
            AssistantMessage(
                content="The capital of France is Paris. It's a beautiful city with many famous landmarks like the Eiffel Tower.",
                source="agent",
            ),
        ],
        success=True,
        error=None,
        usage=Usage(duration_ms=100, llm_calls=1, tokens_input=50, tokens_output=25),
        metadata={},
    )

    judges = [
        ("ExactMatch (naive)", ExactMatchJudge(answer_strategy="last_content")),
        ("Contains (smart)", ContainsJudge()),
        ("FuzzyMatch (smart)", FuzzyMatchJudge(threshold=0.5)),
    ]

    print(f'\nAgent response: "{trajectory.messages[1].content}"')
    print(f'Expected: "{task.expected_output}"')
    print()

    for judge_name, judge in judges:
        score = await judge.score(trajectory)
        status = "✅ PASS" if score.overall > 5 else "❌ FAIL"
        print(f"{judge_name:<20} | Score: {score.overall:4.1f}/10 | {status}")


async def main():
    """Run all demonstrations."""
    print("🧪 REFERENCE-BASED EVALUATION DEMONSTRATION")
    print("This demo shows the new evaluation capabilities in picoagents")

    await demonstrate_extraction_strategies()
    await show_answer_extraction_benefits()
    await demonstrate_composite_judge()

    # Only run live agent comparison if credentials are available
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if azure_endpoint and api_key:
        await compare_judge_types()
    else:
        print("\n" + "=" * 60)
        print("LIVE AGENT COMPARISON SKIPPED")
        print("=" * 60)
        print(
            "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY to see live agent evaluation"
        )

    print("\n" + "=" * 60)
    print("SUMMARY: NEW EVALUATION FEATURES")
    print("=" * 60)
    print("✅ Reference-based judges: ExactMatch, FuzzyMatch, Contains")
    print("✅ Smart answer extraction: last_non_empty, last_assistant, all_assistant")
    print("✅ Composite judges: Combine multiple judges with weights")
    print("✅ Robust evaluation: Handles tool calls, multi-turn, edge cases")
    print("✅ Comprehensive tests: 14 test cases covering all scenarios")
    print(
        "\nThese features make evaluation more reliable and suitable for production use! 🚀"
    )


if __name__ == "__main__":
    asyncio.run(main())

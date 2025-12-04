#!/usr/bin/env python3
"""
Generate expected answers for evaluation tasks using the research team.

This script uses the AI-driven research team to answer complex questions,
then we can use those answers as expected outputs in the evaluation suite.
"""

import asyncio
import json
import os
from pathlib import Path

from picoagents import Agent
from picoagents.llm import AzureOpenAIChatCompletionClient
from picoagents.orchestration import AIOrchestrator
from picoagents.termination import MaxMessageTermination, TextMentionTermination
from picoagents.tools import RESEARCH_TOOLS_AVAILABLE, RegexTool, ThinkTool
from picoagents.types import OrchestrationResponse

if RESEARCH_TOOLS_AVAILABLE:
    from picoagents.tools._research_tools import (
        GoogleSearchTool,
        WebFetchTool,
        YouTubeCaptionTool,
    )


def get_research_orchestrator():
    """Create AI-driven orchestrator with research-capable agents."""
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")

    if not azure_endpoint or not api_key:
        raise ValueError("Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")

    client = AzureOpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        azure_deployment=deployment,
    )

    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")

    planner = Agent(
        name="planner",
        description="Research strategist who breaks down complex questions",
        instructions="Analyze questions and create clear research plans. Be concise (3-5 steps max).",
        model_client=client,
        tools=[ThinkTool()],
    )

    gatherer_tools = [ThinkTool()]
    if RESEARCH_TOOLS_AVAILABLE and google_api_key and google_cse_id:
        gatherer_tools.append(GoogleSearchTool(api_key=google_api_key, cse_id=google_cse_id))  # type: ignore
    if RESEARCH_TOOLS_AVAILABLE:
        gatherer_tools.extend([WebFetchTool(), YouTubeCaptionTool()])  # type: ignore

    gatherer = Agent(
        name="gatherer",
        description="Information gatherer with web search capabilities",
        instructions="Search, fetch content, extract key information systematically.",
        model_client=client,
        tools=gatherer_tools,  # type: ignore
    )

    analyzer = Agent(
        name="analyzer",
        description="Content analyst who extracts specific information",
        instructions="Extract relevant passages, quotes, and patterns. Be precise.",
        model_client=client,
        tools=[ThinkTool(), RegexTool()],
    )

    synthesizer = Agent(
        name="synthesizer",
        description="Research synthesizer who composes coherent answers",
        instructions="Compose clear, factual answers with quotes and attributions. End with: RESEARCH_COMPLETE",
        model_client=client,
        tools=[ThinkTool()],
    )

    termination = MaxMessageTermination(max_messages=25) | TextMentionTermination(
        text="RESEARCH_COMPLETE"
    )

    return AIOrchestrator(
        agents=[planner, gatherer, analyzer, synthesizer],
        termination=termination,
        model_client=client,
        max_iterations=15,
    )


async def research_question(orchestrator, question: str) -> dict:
    """Research a question and return the answer with metadata."""
    print(f"\n{'='*70}")
    print(f"RESEARCHING: {question[:80]}...")
    print(f"{'='*70}\n")

    answer = None
    metadata = {}

    async for item in orchestrator.run_stream(question, verbose=False):
        if isinstance(item, OrchestrationResponse):
            answer = item.final_result
            metadata = {
                "total_messages": len(item.messages),
                "agents_used": item.pattern_metadata.get("unique_agents_selected", 0),
                "workflow": " → ".join(
                    [sel["agent"] for sel in item.pattern_metadata.get("selection_history", [])]
                ),
            }

    return {
        "question": question,
        "expected_answer": answer,
        "research_metadata": metadata,
    }


async def main():
    """Generate expected answers for tool-heavy evaluation tasks."""

    orchestrator = get_research_orchestrator()

    # Define the research questions we want answered
    research_tasks = [
        # Task 1: Podcast Research (your original)
        """Did Andrej Karpathy have a podcast interview with Dwarkesh Patel
        where he discussed Eureka Labs? If so, what did he say was the primary
        goal of Eureka Labs? Provide specific quotes if possible.""",

        # Task 2: Recent Tech Event
        """What were the key announcements from OpenAI's most recent DevDay
        conference? Include the date of the event and list at least 3 major
        announcements with brief descriptions. If there was a DevDay in 2025,
        report on that one; otherwise report on the 2024 DevDay.""",

        # Task 3: Academic Paper Analysis
        """Find a recent paper (2024 or 2025) on arXiv about 'multi-agent reinforcement learning'.
        What is the title, authors, and main contribution of one of the top recent results?
        Does the paper mention any publicly available code repository?""",
    ]

    print("\n" + "="*70)
    print("GENERATING EXPECTED ANSWERS FOR EVALUATION TASKS")
    print("="*70)
    print(f"\nTotal questions: {len(research_tasks)}")
    print("This will take several minutes as each question requires web research...\n")

    results = []
    for i, question in enumerate(research_tasks, 1):
        print(f"\n[{i}/{len(research_tasks)}] ", end="")
        result = await research_question(orchestrator, question)
        results.append(result)

        # Show preview
        preview = result["expected_answer"][:200] + "..." if len(result["expected_answer"]) > 200 else result["expected_answer"]
        print(f"\n✅ Answer preview: {preview}")
        print(f"   Metadata: {result['research_metadata']}")

    # Save results to JSON file
    output_file = Path(__file__).parent / "expected_answers.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*70)
    print("RESULTS SAVED")
    print("="*70)
    print(f"\nExpected answers saved to: {output_file}")
    print("\nYou can now use these answers in create_tool_heavy_tasks() in comprehensive-evaluation.py")

    # Print formatted for easy copy-paste
    print("\n" + "="*70)
    print("FORMATTED FOR EVAL TASKS")
    print("="*70)

    for i, result in enumerate(results, 1):
        print(f"\n# Task {i}")
        print(f'EvalTask(')
        print(f'    name="Tool-Heavy-{i}",')
        print(f'    input="""{result["question"]}""",')
        print(f'    expected_output="""{result["expected_answer"][:300]}...""",  # Truncated, see expected_answers.json')
        print(f'),')

    # IMPORTANT: Manual verification reminder
    print("\n" + "="*70)
    print("⚠️  VERIFICATION REQUIRED")
    print("="*70)
    print("""
IMPORTANT: Please manually verify these answers before using them in evaluation:

1. Check the expected_answers.json file
2. Verify facts against authoritative sources:
   - For podcast task: Check actual Dwarkesh Podcast with Karpathy
   - For OpenAI DevDay: Verify against official OpenAI announcements
   - For arXiv paper: Verify the paper actually exists and details are correct

3. Look for hallucinations:
   - Fabricated quotes
   - Wrong dates
   - Incorrect attributions
   - Made-up paper titles/authors

4. Only use answers you've independently verified as factually correct!

The research team is good but can make mistakes. Human verification is essential.
""")


if __name__ == "__main__":
    print("\n⚠️  NOTE: This requires:")
    print("   - AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
    print("   - GOOGLE_API_KEY and GOOGLE_CSE_ID (for web search)")
    print("   - This will make multiple API calls and may take 5-10 minutes\n")

    asyncio.run(main())

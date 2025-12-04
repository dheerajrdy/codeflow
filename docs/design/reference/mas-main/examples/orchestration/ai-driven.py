#!/usr/bin/env python3
"""
AI-driven orchestration example using AISelectorOrchestrator.

This example demonstrates intelligent agent selection where an LLM
chooses which agent should respond next based on conversation context.
"""

import asyncio

from picoagents import Agent
from picoagents.llm import OpenAIChatCompletionClient
from picoagents.orchestration import AIOrchestrator
from picoagents.termination import MaxMessageTermination, TextMentionTermination
from picoagents.types import OrchestrationResponse


def get_orchestrator():
    """Create AI-driven orchestrator for writing tasks."""

    client = OpenAIChatCompletionClient(model="gpt-4.1-mini")

    writer = Agent(
        name="writer",
        description="Creative writer who crafts engaging content based on user request",
        instructions="""You are a creative writer. Use research provided by others to write
        engaging, well-structured content. Focus on clear organization, compelling narrative,
        and readability. When you see research, turn it into polished prose. Be conscise and brief - 4 lines max!""",
        model_client=client,
    )

    editor = Agent(
        name="editor",
        description="Editor who reviews content for clarity, flow.",
        instructions="""You are an editor. Review written content for clarity, grammar, flow,
        and overall quality. If needed, provide specific suggestions for improvement 3 bullet points no more. If suggestions are addressed and looks good, respond with 'APPROVED'.""",
        model_client=client,
    )

    # Create termination condition
    termination = MaxMessageTermination(max_messages=10) | TextMentionTermination(
        text="APPROVED"
    )

    # Create AI orchestrator - it will intelligently choose who goes next
    orchestrator = AIOrchestrator(
        agents=[writer, editor],
        termination=termination,
        model_client=client,  # LLM for agent selection
        max_iterations=10,
    )

    return orchestrator


orchestrator = get_orchestrator()


async def main():
    """Demonstrate AI-driven agent selection for writing a blog post."""

    task = "Write a note about the benefits of remote work for productivity"

    # Run orchestration with streaming to see the selection process
    async for item in orchestrator.run_stream(task, verbose=False):
        if isinstance(item, OrchestrationResponse):
            print(f"Final output: {item.final_result}")
            print(f"Stop reason: {item.stop_message.content}")
            print(f"Total messages: {len(item.messages)}")

            # Show AI orchestrator specific metadata
            metadata = item.pattern_metadata
            print(f"\n📊 AI Orchestrator Analytics:")
            print(
                f"   • Agents used: {metadata.get('unique_agents_selected', 0)}/{len(orchestrator.agents)}"
            )
            print(f"   • Agent diversity: {metadata.get('agent_diversity', 0):.1%}")
            print(
                f"   • Average confidence: {metadata.get('average_confidence', 0):.2f}"
            )
            print(f"   • Selection model: {metadata.get('model_used', 'unknown')}")

            if "selection_history" in metadata and metadata["selection_history"]:
                print(
                    f"   • Selection sequence: {' → '.join([sel['agent'] for sel in metadata['selection_history']])}"
                )
        else:
            # Handle other event types (orchestration events, etc.)
            print(f" {item}    ")


if __name__ == "__main__":
    asyncio.run(main())

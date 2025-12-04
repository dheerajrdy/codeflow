#!/usr/bin/env python3
"""
Plan-based orchestration example using PlanBasedOrchestrator.

This example demonstrates how the orchestrator creates an execution plan
with agent assignments and tracks step progress with retry logic.
"""

import asyncio

from picoagents import Agent
from picoagents.llm import OpenAIChatCompletionClient
from picoagents.orchestration import PlanBasedOrchestrator
from picoagents.termination import MaxMessageTermination, TextMentionTermination
from picoagents.types import OrchestrationResponse


def get_orchestrator():
    """Create plan-based orchestrator for research and writing tasks."""

    client = OpenAIChatCompletionClient(model="gpt-4.1-mini")

    # Create specialized agents
    researcher = Agent(
        name="researcher",
        description="Research specialist who gathers and analyzes information from various sources",
        instructions="""You are a research specialist. Focus on finding accurate, relevant information.
        Always provide sources and verify facts. Be thorough but concise - aim for 2-3 key points max.""",
        model_client=client,
    )

    writer = Agent(
        name="writer",
        description="Technical writer who creates clear, well-structured documentation",
        instructions="""You are a technical writer. Transform research into clear, engaging content.
        Use proper structure with headers, bullet points. Focus on clarity and readability.
        Keep it concise but informative - 203 sentences max per section.""",
        model_client=client,
    )

    reviewer = Agent(
        name="reviewer",
        description="Quality reviewer who evaluates content for accuracy and completeness",
        instructions="""You are a quality reviewer. Check content for accuracy, clarity, and completeness.
        Provide specific feedback if improvements needed, or respond 'APPROVED' if content meets standards.
        Focus on factual accuracy and clear communication.""",
        model_client=client,
    )

    # Create termination condition
    termination = MaxMessageTermination(max_messages=15) | TextMentionTermination(
        text="APPROVED"
    )

    # Create plan-based orchestrator
    orchestrator = PlanBasedOrchestrator(
        agents=[researcher, writer, reviewer],
        termination=termination,
        model_client=client,  # LLM for planning and evaluation
        max_iterations=15,
        max_step_retries=2,
    )

    return orchestrator


orchestrator = get_orchestrator()


async def main():
    """Demonstrate plan-based orchestration for a multi-step research task."""

    task = "Research and write a comprehensive guide about the benefits of renewable energy sources"

    print("🎯 Starting Plan-Based Orchestration...")
    print(f"Task: {task}\n")

    # Run orchestration with streaming to see the planning process
    step_count = 0
    async for item in orchestrator.run_stream(task, verbose=True):
        if isinstance(item, OrchestrationResponse):
            print(f"\n✅ Final Result: {item.final_result}")
            print(f"Stop reason: {item.stop_message.content}")
            print(f"Total messages: {len(item.messages)}")

            # Show plan-based orchestrator specific metadata
            metadata = item.pattern_metadata
            print(f"\n📊 Plan Orchestrator Analytics:")
            print(f"   • Steps completed: {metadata.get('steps_completed', 0)}")
            print(f"   • Steps failed: {metadata.get('steps_failed', 0)}")
            print(f"   • Total retries: {metadata.get('total_retries', 0)}")
            print(f"   • Current step: {metadata.get('current_step_index', 0) + 1}")

            # Display the execution plan
            if "plan" in metadata and metadata["plan"]:
                plan = metadata["plan"]
                print(f"\n📋 Execution Plan Generated:")
                for i, step in enumerate(plan.steps, 1):
                    status = "✅" if i <= metadata.get("steps_completed", 0) + 1 else "⏳"
                    print(f"   {status} Step {i}: {step.task}")
                    print(f"       Agent: {step.agent_name}")
                    print(f"       Reasoning: {step.reasoning}")
        else:
            print(f"{item}")


if __name__ == "__main__":
    asyncio.run(main())

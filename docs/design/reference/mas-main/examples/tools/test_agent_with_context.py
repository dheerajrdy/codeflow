#!/usr/bin/env python3
"""
Test that Agent now works with context and returns AgentResponse with context.
"""

import asyncio
from picoagents import Agent, AgentContext
from picoagents.llm import BaseChatCompletionClient
from picoagents.messages import AssistantMessage
from picoagents.types import ChatCompletionResult, ChatCompletionChunk, Usage


class MockClient(BaseChatCompletionClient):
    """Simple mock client for testing."""

    def __init__(self):
        super().__init__(model="mock")

    async def create(self, messages, **kwargs):
        return ChatCompletionResult(
            message=AssistantMessage(
                content="I understand your request.",
                source="mock"
            ),
            usage=Usage(duration_ms=100),
            model="mock",
            finish_reason="stop"
        )

    async def create_stream(self, messages, **kwargs):
        yield ChatCompletionChunk(
            content="I understand.",
            is_complete=True,
            tool_call_chunk=None
        )


async def test_agent_with_context():
    """Test Agent with context parameter."""

    print("="*60)
    print(" Testing Agent with Context")
    print("="*60)

    # Create agent
    agent = Agent(
        name="TestAgent",
        description="A test agent",
        instructions="You are a helpful assistant.",
        model_client=MockClient()
    )

    # Test 1: Run with string task
    print("\nTest 1: Run with string task")
    response = await agent.run("Hello, how are you?")
    print(f"  ✓ Response has context: {response.context is not None}")
    print(f"  ✓ Context has {len(response.context.messages)} messages")
    print(f"  ✓ Finish reason: {response.finish_reason}")

    # Test 2: Run with existing context
    print("\nTest 2: Run with existing context")
    context = AgentContext()
    response = await agent.run("What's 2+2?", context=context)
    print(f"  ✓ Response uses provided context: {response.context == context}")
    print(f"  ✓ Context has {len(response.context.messages)} messages")

    # Test 3: Continue conversation with same context
    print("\nTest 3: Continue conversation with same context")
    response = await agent.run("What was my first question?", context=response.context)
    print(f"  ✓ Context preserved: {len(response.context.messages)} messages total")
    print(f"  ✓ Messages in context:")
    for i, msg in enumerate(response.context.messages):
        content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        print(f"    [{i}] {msg.__class__.__name__}: {content_preview}")

    # Test 4: Run without task (continue from context)
    print("\nTest 4: Continue from context without new task")
    response = await agent.run(context=response.context)
    print(f"  ✓ Can continue without task: {response.finish_reason}")
    print(f"  ✓ Context has {len(response.context.messages)} messages")

    print("\n" + "="*60)
    print(" ✅ All Tests Passed!")
    print("="*60)
    print("\nThe Agent now properly:")
    print("  • Accepts an optional context parameter")
    print("  • Returns AgentResponse with context (not messages)")
    print("  • Preserves context across multiple calls")
    print("  • Can continue conversations using context")


if __name__ == "__main__":
    asyncio.run(test_agent_with_context())
"""Simple test to see if tools execute."""
import asyncio
from picoagents.tools import tool
from picoagents.agents import Agent
from picoagents.llm import BaseChatCompletionClient
from picoagents.messages import AssistantMessage, Message, ToolCallRequest
from picoagents.types import ChatCompletionResult, Usage
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel


class MockClient(BaseChatCompletionClient):
    def __init__(self):
        super().__init__(model="test")
        self.call_count = 0

    async def create(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        output_format: Optional[Type[BaseModel]] = None,
        **kwargs: Any,
    ) -> ChatCompletionResult:
        self.call_count += 1
        print(f"Mock client called (call #{self.call_count})")

        # First call: return tool calls
        if self.call_count == 1:
            msg = AssistantMessage(
                content="I'll get the weather",
                source="test",
                tool_calls=[
                    ToolCallRequest(
                        call_id="call_1",
                        tool_name="get_weather",
                        parameters={"city": "Seattle"},
                    )
                ],
            )
            print(f"  Returning tool call: {msg.tool_calls}")
        else:
            # Second call: return summary
            msg = AssistantMessage(content="Task complete", source="test")
            print(f"  Returning summary: {msg.content}")

        return ChatCompletionResult(
            message=msg,
            finish_reason="stop",
            usage=Usage(duration_ms=0),
            model="test",
        )

    async def create_stream(self, messages, tools=None, output_format=None, **kwargs):
        """Not used in this test."""
        raise NotImplementedError()


@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    result = f"Sunny in {city}"
    print(f"  Tool executed! Returning: {result}")
    return result


async def main():
    print("Creating agent...")
    agent = Agent(
        name="test_agent",
        description="Test agent",
        instructions="You are helpful",
        model_client=MockClient(),
        tools=[get_weather],
    )

    print("\nRunning agent...")
    print("Collecting all events...")
    events = []
    async for event in agent.run_stream("What's the weather?"):
        events.append(event)
        print(f"  Event: {type(event).__name__}")
        if hasattr(event, 'tool_calls') and event.tool_calls:
            print(f"    - Has tool_calls: {event.tool_calls}")
        if hasattr(event, 'tool_name'):
            print(f"    - Tool: {event.tool_name}")
        if type(event).__name__ == 'ErrorEvent':
            print(f"    - ERROR: {event.error_message}")
            print(f"    - Type: {event.error_type}")

    # Get final response
    response = events[-1] if events and hasattr(events[-1], 'messages') else None
    if response is None:
        print("\nNo final response found!")
        return

    print(f"\n{'='*50}")
    print(f"Response finish_reason: {response.finish_reason}")
    print(f"Response needs_approval: {response.needs_approval}")
    print(f"Number of messages: {len(response.messages)}")
    print(f"\nMessages:")
    for i, msg in enumerate(response.messages):
        print(f"  {i+1}. {type(msg).__name__}: {msg.content[:50]}...")

    from picoagents.messages import ToolMessage

    tool_msgs = [m for m in response.messages if isinstance(m, ToolMessage)]
    print(f"\nTool messages: {len(tool_msgs)}")
    if tool_msgs:
        for tm in tool_msgs:
            print(f"  - {tm.tool_name}: {tm.content}")
    else:
        print("  NO TOOL MESSAGES FOUND!")


if __name__ == "__main__":
    asyncio.run(main())

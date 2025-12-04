"""Quick debug script to test middleware streaming."""
import asyncio
from picoagents._middleware import MiddlewareChain
from picoagents.context import AgentContext
from picoagents.types import ToolResult

async def main():
    # Test that execute_stream yields results correctly
    chain = MiddlewareChain([])
    context = AgentContext()

    async def mock_func(data):
        return ToolResult(result="test", success=True, error=None)

    tool_result = None
    print("Starting stream...")
    async for item in chain.execute_stream(
        operation="tool_call",
        agent_name="test",
        agent_context=context,
        data={},
        func=mock_func,
    ):
        print(f"Got item: {type(item)} - {item}")
        if isinstance(item, ToolResult):
            tool_result = item
            print(f"Found ToolResult: {tool_result}")

    print(f"Final tool_result: {tool_result}")
    assert tool_result is not None, "ToolResult was not yielded!"
    print("✓ Test passed")

if __name__ == "__main__":
    asyncio.run(main())

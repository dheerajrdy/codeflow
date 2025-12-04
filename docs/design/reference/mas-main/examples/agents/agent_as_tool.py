"""
Agent as Tool composition example.
Shows how specialized agents can be used as tools by coordinator agents.
"""

import asyncio
import os

from picoagents import Agent
from picoagents.llm import AzureOpenAIChatCompletionClient


def get_weather(location: str) -> str:
    """Get current weather for a given location."""
    return f"The weather in {location} is sunny, 100F"


def analyze_data(data: str) -> str:
    """Analyze the provided data and return insights."""
    return f"Analysis of '{data}': This shows positive trends with seasonal variations."


# Create Azure client
model_client = AzureOpenAIChatCompletionClient(
    azure_deployment="gpt-4.1-mini",
    azure_endpoint=os.environ.get(
        "AZURE_OPENAI_ENDPOINT", "https://your-endpoint.openai.azure.com/"
    ),
)


def tool_agents():
    """Create specialized agents to be used as tools."""
    # Specialized weather agent
    weather_agent = Agent(
        name="weather_specialist",
        description="Specialized agent for weather information",
        instructions="You provide weather information using available tools. Be concise.",
        model_client=model_client,
        tools=[get_weather],
    )

    # Specialized analysis agent
    analysis_agent = Agent(
        name="data_analyst",
        description="Specialized agent for data analysis",
        instructions="You analyze data and provide insights. Be analytical.",
        model_client=model_client,
        tools=[analyze_data],
    )
    return weather_agent, analysis_agent


weather_agent, analysis_agent = tool_agents()
print(f"Created specialist agents: {weather_agent.name}, {analysis_agent.name}")


# Create coordinator that uses both specialists as tools
# Note: You can control how results are extracted using result_strategy:
# - "last" (default): Returns only the final message
# - "last:N": Returns last N messages concatenated
# - "all": Returns all messages
# - Custom callable: Function that processes messages and returns a string
agent = Agent(
    name="research_coordinator",
    description="Coordinates research tasks using specialist agents",
    instructions="You solve tasks by delegating to the relevant agents or tools",
    model_client=model_client,
    tools=[
        weather_agent.as_tool(),  # Default: last message only
        analysis_agent.as_tool(result_strategy="last:2"),  # Last 2 messages
    ],
    example_tasks=[
        "Get the current weather in New York and analyze recent sales data.",
        "Provide a brief report on the weather in San Francisco and its impact on outdoor events.",
    ],
)


async def main():
    """Run the agent composition example."""

    print("=== AGENT AS TOOL COMPOSITION EXAMPLE ===", "\n" + "=" * 50)
    # Complex task requiring both specialists
    complex_task = "Write a very brief health report on the current weather in SF."

    # Stream the coordinator's execution
    async for event in agent.run_stream(complex_task):
        print(event)


if __name__ == "__main__":
    asyncio.run(main())

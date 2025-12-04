"""
GitHub Models Agent Example

Shows how to use GitHub Models with PicoAgents via base_url.
Requires: GITHUB_TOKEN environment variable

Run: python examples/agents/agent_githubmodels.py
"""

import asyncio
import os

from picoagents import Agent, OpenAIChatCompletionClient


def get_weather(location: str) -> str:
    """Get current weather for a given location."""
    return f"The weather in {location} is sunny, 75°F"


# Create agent with GitHub Models endpoint
agent = Agent(
    name="github_models_assistant",
    description="An assistant powered by GitHub Models",
    instructions="You are a helpful assistant with weather access.",
    model_client=OpenAIChatCompletionClient(
        model="openai/gpt-4.1-mini",
        api_key=os.getenv("GITHUB_TOKEN"),
        base_url="https://models.github.ai/inference"
    ),
    tools=[get_weather],
    example_tasks=[
        "What's the weather in San Francisco?",
        "Is it sunny in Tokyo?",
    ],
)


async def main():
    """Run example with GitHub Models."""
    print("=== GitHub Models Agent ===\n")

    async for event in agent.run_stream(
        "What's the weather in Paris?",
        stream_tokens=False
    ):
        print(event)


if __name__ == "__main__":
    if not os.getenv("GITHUB_TOKEN"):
        print("Set GITHUB_TOKEN environment variable first")
    else:
        asyncio.run(main())
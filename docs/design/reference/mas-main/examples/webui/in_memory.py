"""
Example: Serving in-memory entities with PicoAgents WebUI.

This example demonstrates how to create agents and orchestrators in code
and serve them via the web interface using the simple serve() API.

Run with: python examples/webui/in_memory.py
"""

import os
from picoagents import Agent
from picoagents.llm._azure_openai import AzureOpenAIChatCompletionClient
from picoagents.orchestration import RoundRobinOrchestrator
from picoagents.termination import MaxMessageTermination
from picoagents.tools import tool, ApprovalMode
from picoagents.webui import serve


# Define simple tools
def get_weather(location: str) -> str:
    """Get current weather for a given location."""
    return f"The weather in {location} is sunny and 72°F"


def calculate(expression: str) -> str:
    """Perform basic mathematical calculations.

    Args:
        expression: Math expression to evaluate (e.g., "2 + 2", "15 * 3")
    """
    try:
        result = eval(expression)
        return f"The result is {result}"
    except Exception as e:
        return f"Error: {e}"


# Tools that require approval
@tool(approval_mode=ApprovalMode.ALWAYS)
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient. Requires approval before sending.

    Args:
        to: Email address of recipient
        subject: Email subject line
        body: Email body content
    """
    return f"Email sent to {to} with subject '{subject}'"


@tool(approval_mode=ApprovalMode.ALWAYS)
def delete_file(path: str) -> str:
    """Delete a file. Requires approval before deletion.

    Args:
        path: Path to the file to delete
    """
    return f"File deleted: {path}"


# Create a weather assistant agent
weather_agent = Agent(
    name="weather_assistant",
    description="Provides weather information for locations",
    instructions="You are a helpful weather assistant. Use the get_weather tool to provide weather information.",
    model_client= AzureOpenAIChatCompletionClient(
    azure_deployment="gpt-4.1-mini",
    azure_endpoint=os.environ.get(
        "AZURE_OPENAI_ENDPOINT", "https://your-endpoint.openai.azure.com/"
    ),
),
    tools=[get_weather],
)

# Create a math assistant agent
math_agent = Agent(
    name="math_assistant",
    description="Helps with mathematical calculations",
    instructions="You are a helpful math assistant. Use the calculate tool to solve math problems.",
    model_client= AzureOpenAIChatCompletionClient(
    azure_deployment="gpt-4.1-mini",
    azure_endpoint=os.environ.get(
        "AZURE_OPENAI_ENDPOINT", "https://your-endpoint.openai.azure.com/"
    ),
),
    tools=[calculate],
)

# Create a general assistant with both tools
general_agent = Agent(
    name="general_assistant",
    description="General purpose assistant with weather and math capabilities",
    instructions="You are a helpful assistant with access to weather and calculation tools.",
    model_client= AzureOpenAIChatCompletionClient(
    azure_deployment="gpt-4.1-mini",
    azure_endpoint=os.environ.get(
        "AZURE_OPENAI_ENDPOINT", "https://your-endpoint.openai.azure.com/"
    ),
),
    tools=[get_weather, calculate],
)

# Create an orchestrator coordinating both specialized agents
assistant_team = RoundRobinOrchestrator(
    agents=[weather_agent, math_agent],
    termination=MaxMessageTermination(max_messages=10),
)

# Create an agent with approval-required tools
approval_agent = Agent(
    name="approval_demo",
    description="Demo agent with tool approval - test the approval dialog",
    instructions="""You are a helpful assistant with access to tools.

When asked to perform an action:
1. ALWAYS call the appropriate tool immediately
2. Do NOT ask for permission - the approval system will handle that
3. Use send_email for email tasks
4. Use delete_file for file deletion
5. Use get_weather for weather information

Be direct and use tools without hesitation.""",
    model_client=AzureOpenAIChatCompletionClient(
        azure_deployment="gpt-4.1-mini",
        azure_endpoint=os.environ.get(
            "AZURE_OPENAI_ENDPOINT", "https://your-endpoint.openai.azure.com/"
        ),
    ),
    tools=[send_email, delete_file, get_weather],
)

if __name__ == "__main__":
    # Serve all entities via web interface
    print("🚀 Starting PicoAgents WebUI with in-memory entities...")
    print("\n📋 Available entities:")
    print("  • weather_assistant (Agent) - Weather information")
    print("  • math_assistant (Agent) - Math calculations")
    print("  • general_assistant (Agent) - Weather + Math")
    print("  • assistant_team (Orchestrator) - Coordinated team")
    print("  • approval_demo (Agent) - Test tool approval flow\n")

    # Serve only these in-memory entities (no directory scanning)
    serve(
        entities=[weather_agent, math_agent, general_agent, assistant_team, approval_agent],
        port=8070,
        auto_open=True,
    )
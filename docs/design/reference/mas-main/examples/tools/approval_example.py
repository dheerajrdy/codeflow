"""
Example demonstrating tool approval functionality in PicoAgents.

This example shows how to:
1. Create tools that require approval
2. Handle approval requests from agents
3. Continue execution after approval/rejection
"""

import asyncio 
from typing import List
import os
from picoagents import Agent, AgentContext
from picoagents.llm import AzureOpenAIChatCompletionClient
from picoagents.tools import ApprovalMode, tool

azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")


# Define tools with different approval modes
@tool
def get_weather(city: str) -> str:
    """Get weather information for a city."""
    # Simulated weather API call
    return f"Weather in {city}: Sunny, 72°F with light winds"


@tool(approval_mode="always_require")
def delete_file(filepath: str) -> str:
    """Delete a file from the filesystem."""
    # In a real implementation, this would delete the file
    # For safety in this example, we just simulate it
    print(f"[SIMULATED] Would delete file: {filepath}")
    return f"Successfully deleted {filepath}"


@tool(approval_mode="always_require")
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient."""
    # Simulated email sending
    print(f"[SIMULATED] Would send email to {to}")
    return f"Email sent to {to} with subject '{subject}'"


async def handle_approvals_interactive(agent: Agent, initial_task: str):
    """
    Handle agent execution with interactive approval prompts.

    This demonstrates the full approval flow:
    1. Agent attempts to execute tools
    2. Tools requiring approval pause execution
    3. User is prompted for approval
    4. Execution continues based on approval/rejection
    """
    print(f"\n{'='*50}")
    print(f"Task: {initial_task}")
    print(f"{'='*50}\n")

    # Create a new context for this conversation
    context = AgentContext()

    # Run the agent with the initial task
    response = await agent.run(initial_task, context=context)

    # Check if approval is needed
    while response.needs_approval:
        print("\n" + "="*50)
        print("⚠️  APPROVAL REQUIRED")
        print("="*50)

        # Process each approval request
        for i, approval_req in enumerate(response.approval_requests, 1):
            print(f"\n[{i}] Tool: {approval_req.tool_name}")
            print(f"    Parameters: {approval_req.parameters}")

            # Get user input
            while True:
                user_input = input(f"    Approve? (y/n): ").lower().strip()
                if user_input in ['y', 'n']:
                    break
                print("    Please enter 'y' for yes or 'n' for no.")

            # Create approval response
            approved = user_input == 'y'
            approval_response = approval_req.create_response(approved=approved)

            # Add to context
            response.context.add_approval_response(approval_response)

            if approved:
                print(f"    ✅ Approved")
            else:
                print(f"    ❌ Rejected")

        print("\nContinuing execution...\n")

        # Continue execution with the updated context
        response = await agent.run(context=response.context)

    # Print final result
    print("\n" + "="*50)
    print("TASK COMPLETED")
    print("="*50)

    # Show the conversation history
    print("\nConversation History:")
    for msg in response.messages[-3:]:  # Show last 3 messages
        role = msg.__class__.__name__.replace("Message", "")
        content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
        print(f"  [{role}]: {content}")

    print(f"\nFinal Status: {response.finish_reason}")
    print(f"Total Duration: {response.usage.duration_ms}ms")

    return response


async def run_examples():
    """Run various example scenarios."""

    # Initialize the LLM client
    # Note: Set your OPENAI_API_KEY environment variable
    try:
        llm_client = AzureOpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        azure_deployment=deployment,
    )

    except Exception as e:
        print(f"Error initializing LLM client: {e}")
        print("Please set your OPENAI_API_KEY environment variable")
        return

    # Create an agent with approval-enabled tools
    agent = Agent(
        name="FileAssistant",
        description="An assistant that can manage files and send emails",
        instructions=(
            "You are a helpful assistant that can check weather, manage files, "
            "and send emails. Always be clear about what actions you're taking."
        ),
        model_client=llm_client,
        tools=[get_weather, delete_file, send_email],
        max_iterations=5
    )

    # Example 1: Task with no approval needed
    print("\n" + "#"*60)
    print("# Example 1: No Approval Required")
    print("#"*60)
    await handle_approvals_interactive(
        agent,
        "What's the weather like in San Francisco?"
    )

    # Example 2: Task requiring approval
    print("\n" + "#"*60)
    print("# Example 2: File Deletion (Approval Required)")
    print("#"*60)
    await handle_approvals_interactive(
        agent,
        "Delete the file /tmp/old_data.csv"
    )

    # Example 3: Multiple tools, mixed approval
    print("\n" + "#"*60)
    print("# Example 3: Mixed Approval Requirements")
    print("#"*60)
    await handle_approvals_interactive(
        agent,
        "Check the weather in New York and then send an email to john@example.com "
        "with the weather report"
    )

    # Example 4: Multiple approval-required tools
    print("\n" + "#"*60)
    print("# Example 4: Multiple Approvals")
    print("#"*60)
    await handle_approvals_interactive(
        agent,
        "Delete /tmp/cache.txt and /tmp/temp.log, then email admin@company.com "
        "to confirm the cleanup is done"
    )


async def run_automated_approval_example():
    """
    Example with automated approval based on policies.

    This shows how you might implement automated approval
    for certain conditions (e.g., auto-approve deletions in /tmp/).
    """
    print("\n" + "#"*60)
    print("# Automated Approval Example")
    print("#"*60)

    try:
        llm_client =  AzureOpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        azure_deployment=deployment,
    )

    except Exception:
        print("Skipping automated example - no API key")
        return

    agent = Agent(
        name="AutomatedAssistant",
        description="Assistant with automated approval policies",
        instructions="You help with file management tasks.",
        model_client=llm_client,
        tools=[delete_file, send_email]
    )

    # Define approval policy
    def auto_approve_policy(approval_request):
        """Auto-approve safe operations."""
        # Auto-approve deletions in /tmp/
        if approval_request.tool_name == "delete_file":
            filepath = approval_request.parameters.get("filepath", "")
            if filepath.startswith("/tmp/"):
                return True

        # Auto-reject emails to certain domains
        if approval_request.tool_name == "send_email":
            to = approval_request.parameters.get("to", "")
            if "@spam.com" in to:
                return False

        # For everything else, require manual approval
        return None  # None means manual approval needed

    # Run with automated policy
    task = "Delete /tmp/test.txt and /home/user/important.doc"
    print(f"\nTask: {task}\n")

    context = AgentContext()
    response = await agent.run(task, context=context)

    while response.needs_approval:
        print("Processing approval requests...")

        for approval_req in response.approval_requests:
            # Apply automated policy
            auto_decision = auto_approve_policy(approval_req)

            if auto_decision is not None:
                # Automated decision
                approved = auto_decision
                print(f"  [{approval_req.tool_name}] Auto-{'approved' if approved else 'rejected'}")
            else:
                # Manual approval needed
                print(f"  [{approval_req.tool_name}] Requires manual approval")
                print(f"    Parameters: {approval_req.parameters}")
                user_input = input("    Approve? (y/n): ").lower().strip()
                approved = user_input == 'y'

            # Add approval response
            approval_response = approval_req.create_response(approved=approved)
            response.context.add_approval_response(approval_response)

        # Continue execution
        response = await agent.run(context=response.context)

    print(f"\nTask completed: {response.finish_reason}")


async def main():
    """Run all examples."""

    print("="*60)
    print(" PicoAgents Tool Approval Examples")
    print("="*60)
    print()
    print("This example demonstrates:")
    print("1. Tools without approval (execute immediately)")
    print("2. Tools requiring approval (pause for user input)")
    print("3. Mixed approval scenarios")
    print("4. Automated approval policies")
    print()

    # Run interactive examples
    await run_examples()

    # Run automated approval example
    await run_automated_approval_example()

    print("\n" + "="*60)
    print(" Examples Complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
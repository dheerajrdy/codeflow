"""
MCP Integration Example with Tool Approvals.

This example demonstrates how to use MCP filesystem tools with PicoAgents,
including the approval system for sensitive operations.

The example shows:
1. Connecting to an MCP filesystem server
2. Discovering and using MCP tools
3. Enabling approval mode for write/delete operations
4. Two tasks:
   - Task 1: Analyze directory contents (read-only, no approval needed)
   - Task 2: Create a sample file (requires approval)

This demonstrates how approval mode provides a safety layer for destructive
operations while allowing read operations to proceed automatically.

Prerequisites:
    pip install picoagents[mcp]
    # For MCP filesystem server, you need Node.js:
    npx @modelcontextprotocol/server-filesystem

Environment:
    OPENAI_API_KEY or AZURE_OPENAI_API_KEY must be set

Usage:
    # Use default location (Desktop)
    python examples/mcp/basic_mcp_agent.py

    # Or specify a custom directory
    python examples/mcp/basic_mcp_agent.py ~/Documents
"""

import asyncio
import os
import sys
from pathlib import Path

from picoagents import Agent
from picoagents.llm import AzureOpenAIChatCompletionClient, OpenAIChatCompletionClient
from picoagents.tools import ApprovalMode, MCP_AVAILABLE, StdioServerConfig, create_mcp_tools


async def main():
    """Run the folder organization recommender example."""

    # Check if MCP is available
    if not MCP_AVAILABLE:
        print("❌ MCP not installed. Install with: pip install picoagents[mcp]")
        return

    print("🚀 Starting Folder Organization Recommender\n")

    # Determine directory to analyze
    # Use Desktop as default, or accept custom path from command line
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1]).expanduser().resolve()
    else:
        target_dir = Path.home() / "Desktop"

    if not target_dir.exists():
        print(f"❌ Directory does not exist: {target_dir}")
        return

    print(f"📁 Analyzing directory: {target_dir}\n")

    # Configure MCP filesystem server with read-only access
    # This server provides tools for reading files and listing directories
    filesystem_config = StdioServerConfig(
        server_id="filesystem",
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-filesystem",
            str(target_dir),  # Use absolute path to target directory
        ],
    )

    # Create MCP tools
    print("📡 Connecting to MCP filesystem server...")
    manager, mcp_tools = await create_mcp_tools([filesystem_config])

    print(f"✅ Connected! Discovered {len(mcp_tools)} tools:")
    for tool in mcp_tools:
        # Truncate long descriptions
        desc = tool.description[:80] + "..." if len(tool.description) > 80 else tool.description
        print(f"   - {tool.name}: {desc}")

    # Enable approval mode for write/delete operations
    # This requires user approval before executing sensitive operations
    for tool in mcp_tools:
        if "write" in tool.name or "delete" in tool.name or "create" in tool.name:
            tool.approval_mode = ApprovalMode.ALWAYS
            print(f"   ⚠️  Approval required for: {tool.name}")

    print("\n🤖 Creating folder organization agent...\n")

    # Create model client (try Azure first, fall back to OpenAI)
    if os.getenv("AZURE_OPENAI_API_KEY"):
        model_client = AzureOpenAIChatCompletionClient(
            model="gpt-4.1-mini",
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv(
                "AZURE_OPENAI_ENDPOINT", "https://YOUR_ENDPOINT.openai.azure.com"
            ),
            api_version="2024-08-01-preview",
        )
    elif os.getenv("OPENAI_API_KEY"):
        model_client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    else:
        print("❌ Please set OPENAI_API_KEY or AZURE_OPENAI_API_KEY")
        await manager.disconnect_all()
        return

    # Create agent with filesystem access
    agent = Agent(
        name="filesystem_agent",
        description="An agent that can analyze folders and perform file operations.",
        instructions="Use the available filesystem tools to complete tasks as requested. Always be helpful and clear about what you're doing.",
        model_client=model_client,
        tools=mcp_tools,
        system_message=f"""You are a helpful assistant with access to filesystem tools for {target_dir}.

You can read files, list directories, and write files. Some operations require user approval for safety.

Be clear and concise in your responses.""",
    )

    # Task 1: Analyze and recommend organization
    print("📝 Task 1: Analyzing folder structure...\n")
    task1 = "Please analyze the files in this directory and provide a brief summary of what's here and how it could be better organized."

    response = await agent.run(task1)
    print(response.messages[-1].content)
    print("\n" + "=" * 60 + "\n")

    # Task 2: Create a sample file (will trigger approval)
    print("📝 Task 2: Creating a sample file (requires approval)...\n")
    task2 = f"Create a file called 'sample.txt' in {target_dir} with the content 'Hello from MCP with approval!'"

    response = await agent.run(task2)

    # Handle approval requests
    while response.needs_approval:
        print("\n" + "=" * 50)
        print("⚠️  APPROVAL REQUIRED")
        print("=" * 50)

        # Process each approval request
        for i, approval_req in enumerate(response.approval_requests, 1):
            print(f"\n[{i}] Tool: {approval_req.tool_name}")
            print(f"    Parameters: {approval_req.parameters}")

            # Get user input
            while True:
                user_input = input(f"    Approve? (y/n): ").lower().strip()
                if user_input in ["y", "n"]:
                    break
                print("    Please enter 'y' for yes or 'n' for no.")

            # Create approval response
            approved = user_input == "y"
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

    print(response.messages[-1].content)
    print("\n" + "=" * 60 + "\n")

    # Cleanup
    print("🧹 Cleaning up...")
    await manager.disconnect_all()
    print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())

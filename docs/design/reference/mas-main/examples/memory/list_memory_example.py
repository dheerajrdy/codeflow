"""
Example: Application-managed memory with ListMemory.

Demonstrates how applications control memory storage and retrieval,
automatically injecting relevant context into agent prompts.

The developer calls memory.add() to store information, and the framework
automatically retrieves and injects context via memory.get_context().
The agent receives this context but does not control what gets stored.
"""

import asyncio

from picoagents import Agent
from picoagents.llm import AzureOpenAIChatCompletionClient
from picoagents.memory import ListMemory, MemoryContent


async def demo_list_memory():
    """
    Demonstrate application-managed memory.

    The application stores user preferences in memory, and the framework
    automatically injects this context into the agent's prompts.
    """
    # Initialize model client
    client = AzureOpenAIChatCompletionClient(model="gpt-4.1-mini")

    # Create memory - application manages storage
    memory = ListMemory(max_memories=100)

    # Application stores user preferences
    await memory.add(
        MemoryContent(
            content="User prefers concise responses without verbose explanations",
            mime_type="text/plain",
        )
    )
    await memory.add(
        MemoryContent(
            content="User works as a Python developer, familiar with async/await",
            mime_type="text/plain",
        )
    )
    await memory.add(
        MemoryContent(
            content="User's timezone is PST (UTC-8)",
            mime_type="text/plain",
        )
    )

    # Create agent with memory - framework handles context injection
    agent = Agent(
        name="assistant",
        description="Helpful programming assistant",
        instructions="""You are a helpful programming assistant.
Use any relevant context from memory to personalize your responses.""",
        model_client=client,
        memory=memory,
    )

    print("=" * 60)
    print("APPLICATION-MANAGED MEMORY DEMO")
    print("=" * 60)
    print()
    print(f"Stored {len(memory.memories)} preferences in memory")
    print()

    # Agent automatically receives memory context
    task = "Explain how to use asyncio.gather()"

    print(f"User: {task}")
    print()

    response = await agent.run(task)

    print(f"{agent.name}: {response.messages[-1].content}")
    print()

    print("=" * 60)
    print("Notice how the agent's response reflects the stored preferences:")
    print("- Concise (no verbose explanations)")
    print("- Assumes Python/async knowledge")
    print("- The agent did NOT call any memory tools")
    print("- The framework automatically injected context")
    print("=" * 60)


async def demo_memory_query():
    """Demonstrate querying memory for relevant context."""
    print("\n" + "=" * 60)
    print("MEMORY QUERY DEMO")
    print("=" * 60)
    print()

    client = AzureOpenAIChatCompletionClient(model="gpt-4.1-mini")
    memory = ListMemory(max_memories=100)

    # Store various facts
    facts = [
        "Project deadline is March 15th",
        "Team meeting every Monday at 10am PST",
        "Code review checklist: tests, docs, type hints",
        "Production deployment happens on Fridays",
        "Database backup runs at 2am daily",
    ]

    for fact in facts:
        await memory.add(MemoryContent(content=fact))

    print(f"Stored {len(memory.memories)} facts in memory")
    print()

    # Query for relevant memories
    query = "when is the deadline"
    results = await memory.query(query, limit=2)

    print(f"Query: '{query}'")
    print(f"Found {len(results.results)} relevant memories:")
    for i, result in enumerate(results.results, 1):
        print(f"  {i}. {result.content}")
    print()

    # The framework uses similar logic internally when preparing prompts
    print("(The framework uses similar querying when injecting context)")


if __name__ == "__main__":
    print("📝 PicoAgents Application-Managed Memory Examples\n")

    asyncio.run(demo_list_memory())
    asyncio.run(demo_memory_query())

    print("\n✨ Examples completed!")
    print("\nNext: Try ChromaDB for semantic search with vector embeddings")
    print("Install: pip install 'picoagents[rag]'")

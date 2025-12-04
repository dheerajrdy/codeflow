#!/usr/bin/env python3
"""
Simple example demonstrating LLM client serialization with picoagents.
"""

import json

from picoagents.agents import Agent
from picoagents.llm import OpenAIChatCompletionClient
from picoagents.memory import FileMemory, ListMemory
from picoagents.orchestration import AIOrchestrator, RoundRobinOrchestrator
from picoagents.termination import (
    CompositeTermination,
    MaxMessageTermination,
    TextMentionTermination,
)
from picoagents.tools import FunctionTool


def test_llm_serialization():
    print("🤖 PicoAgents LLM Client Serialization")
    print("=" * 50)

    # Create an OpenAI client
    client = OpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        api_key="sk-test-key-12345",  # Dummy key for example
    )

    print(f"📱 Created client: {client.__class__.__name__}")
    print(f"📊 Model: {client.model}")

    # Serialize the client to a component model
    component_model = client.dump_component()

    print("\n🔄 Serialized component:")
    print(json.dumps(component_model.model_dump(), indent=2))

    # Load it back
    loaded_client = OpenAIChatCompletionClient.load_component(component_model)

    print(f"\n✅ Loaded client: {loaded_client.__class__.__name__}")
    print(f"📊 Model: {loaded_client.model}")
    print(f"🔑 API Key: {loaded_client.api_key}")

    print("\n🎉 LLM serialization successful!")


def test_memory_serialization():
    print("\n\n🧠 PicoAgents Memory Serialization")
    print("=" * 50)

    # Test ListMemory
    print("\n📝 Testing ListMemory...")
    list_memory = ListMemory(max_memories=100)

    # Serialize empty memory
    component_model = list_memory.dump_component()
    print("✅ ListMemory serialized successfully")

    # Load it back
    loaded_memory = ListMemory.load_component(component_model)
    print(f"✅ Loaded memory: max_memories={loaded_memory.max_memories}")

    # Test FileMemory
    print("\n💾 Testing FileMemory...")
    file_memory = FileMemory("test_memories.json", max_memories=50)

    # Serialize file memory
    component_model = file_memory.dump_component()
    print("✅ FileMemory serialized successfully")

    # Load it back
    loaded_file_memory = FileMemory.load_component(component_model)
    print(f"✅ Loaded file memory: path={loaded_file_memory.file_path}")

    print("\n🎉 Memory serialization successful!")


def test_tools_serialization():
    print("\n\n🔧 PicoAgents Tools Serialization")
    print("=" * 50)

    # Test FunctionTool (should fail)
    print("\n⚡ Testing FunctionTool...")

    def example_function(x: int, y: str = "default") -> str:
        """An example function for testing."""
        return f"Result: {x} - {y}"

    function_tool = FunctionTool(example_function)

    try:
        function_tool.dump_component()
        print("❌ ERROR: FunctionTool serialization should have failed!")
    except NotImplementedError as e:
        print(f"✅ Expected error: {e}")

    print("\n🎉 Tools serialization test successful!")


def test_agent_serialization():
    print("\n\n🤖 PicoAgents Agent Serialization")
    print("=" * 50)

    # Create an agent with model client and memory
    print("\n👤 Creating Agent...")

    model_client = OpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        api_key="sk-test-key-12345",
    )

    memory = ListMemory(max_memories=50)

    agent = Agent(
        name="TestAgent",
        description="A test agent for serialization",
        instructions="You are a helpful test assistant",
        model_client=model_client,
        memory=memory,
        max_iterations=5,
    )

    print(f"✅ Created agent: {agent.name}")
    print(f"📊 Model: {agent.model_client.model}")
    print(f"🧠 Memory: {agent.memory.__class__.__name__}")

    # Serialize the agent
    print("\n🔄 Serializing agent...")
    component_model = agent.dump_component()

    print("✅ Agent serialized successfully")
    print(
        f"📦 Config includes: model_client, memory, {len(component_model.config.get('tools', []))} tools"
    )

    # Load it back
    print("\n📥 Loading agent from config...")
    loaded_agent = Agent.load_component(component_model)

    print(f"✅ Loaded agent: {loaded_agent.name}")
    print(f"📊 Model: {loaded_agent.model_client.model}")
    print(f"🧠 Memory: {loaded_agent.memory.__class__.__name__}")
    print(f"⚙️ Max iterations: {loaded_agent.max_iterations}")

    print("\n🎉 Agent serialization successful!")


def test_termination_serialization():
    print("\n\n🛑 PicoAgents Termination Serialization")
    print("=" * 50)

    # Test MaxMessageTermination
    print("\n📊 Testing MaxMessageTermination...")
    max_msg_term = MaxMessageTermination(max_messages=10)

    component_model = max_msg_term.dump_component()
    print("✅ MaxMessageTermination serialized successfully")

    loaded_term = MaxMessageTermination.load_component(component_model)
    print(f"✅ Loaded termination: max_messages={loaded_term.max_messages}")

    # Test TextMentionTermination
    print("\n📝 Testing TextMentionTermination...")
    text_term = TextMentionTermination("DONE", case_sensitive=True)

    component_model = text_term.dump_component()
    print("✅ TextMentionTermination serialized successfully")

    loaded_text_term = TextMentionTermination.load_component(component_model)
    print(
        f"✅ Loaded termination: text='{loaded_text_term.text}', case_sensitive={loaded_text_term.case_sensitive}"
    )

    # Test CompositeTermination
    print("\n🔗 Testing CompositeTermination...")
    composite_term = CompositeTermination([max_msg_term, text_term], mode="any")

    component_model = composite_term.dump_component()
    print("✅ CompositeTermination serialized successfully")

    loaded_composite = CompositeTermination.load_component(component_model)
    print(
        f"✅ Loaded composite: {len(loaded_composite.conditions)} conditions, mode={loaded_composite.mode}"
    )

    print("\n🎉 Termination serialization successful!")


def test_orchestrator_serialization():
    print("\n\n🎭 PicoAgents Orchestrator Serialization")
    print("=" * 50)

    # Create components for orchestrator
    print("\n⚙️ Creating orchestrator components...")

    # Create model clients
    model_client1 = OpenAIChatCompletionClient(model="gpt-4.1-mini", api_key="sk-test-1")
    model_client2 = OpenAIChatCompletionClient(model="gpt-4.1-mini", api_key="sk-test-2")

    # Create agents
    agent1 = Agent(
        name="Agent1",
        description="First agent",
        instructions="You are agent 1",
        model_client=model_client1,
        memory=ListMemory(max_memories=10),
    )

    agent2 = Agent(
        name="Agent2",
        description="Second agent",
        instructions="You are agent 2",
        model_client=model_client2,
    )

    # Create termination condition
    termination = MaxMessageTermination(max_messages=5)

    # Create orchestrator
    orchestrator = RoundRobinOrchestrator(
        agents=[agent1, agent2], termination=termination, max_iterations=3
    )

    print(f"✅ Created orchestrator with {len(orchestrator.agents)} agents")
    print(f"🛑 Termination: {orchestrator.termination.__class__.__name__}")

    # Serialize orchestrator
    print("\n🔄 Serializing orchestrator...")
    component_model = orchestrator.dump_component()

    print("✅ Orchestrator serialized successfully")
    print(
        f"📦 Config includes: {len(component_model.config.get('agents', []))} agents, termination, max_iterations"
    )

    # Load it back
    print("\n📥 Loading orchestrator from config...")
    loaded_orchestrator = RoundRobinOrchestrator.load_component(component_model)

    print(f"✅ Loaded orchestrator with {len(loaded_orchestrator.agents)} agents")
    print(f"🛑 Termination: {loaded_orchestrator.termination.__class__.__name__}")
    print(f"⚙️ Max iterations: {loaded_orchestrator.max_iterations}")
    print(f"👥 Agent names: {[agent.name for agent in loaded_orchestrator.agents]}")

    print("\n🎉 Orchestrator serialization successful!")

    # Test AIOrchestrator
    print("\n🧠 Testing AIOrchestrator...")

    # Create selector model client (for AI decision making)
    selector_client = OpenAIChatCompletionClient(
        model="gpt-4.1-mini", api_key="sk-selector-key"
    )

    # Create AI orchestrator
    ai_orchestrator = AIOrchestrator(
        agents=[agent1, agent2],
        termination=termination,
        model_client=selector_client,
        max_iterations=4,
    )

    print(f"✅ Created AI orchestrator with {len(ai_orchestrator.agents)} agents")
    print(f"🧠 Selector model: {ai_orchestrator.model_client.model}")

    # Serialize AI orchestrator
    component_model = ai_orchestrator.dump_component()
    print("✅ AIOrchestrator serialized successfully")

    # Load it back
    loaded_ai = AIOrchestrator.load_component(component_model)
    print(f"✅ Loaded AI orchestrator: {len(loaded_ai.agents)} agents")
    print(f"🧠 Selector model: {loaded_ai.model_client.model}")
    print(f"⚙️ Max iterations: {loaded_ai.max_iterations}")

    print("\n🎉 AIOrchestrator serialization successful!")


def main():
    test_llm_serialization()
    test_memory_serialization()
    test_tools_serialization()
    test_termination_serialization()
    test_agent_serialization()
    test_orchestrator_serialization()


if __name__ == "__main__":
    main()

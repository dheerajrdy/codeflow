#!/usr/bin/env python3
"""
AI-driven research team for complex information gathering tasks.

This example demonstrates a multi-agent research team that can:
- Search the web for information
- Fetch and analyze content (web pages, YouTube transcripts)
- Extract specific information from sources
- Synthesize findings into coherent answers

The team uses AI-driven orchestration to intelligently coordinate between
specialized agents based on the research task requirements.
"""

import asyncio
import os

from picoagents import Agent
from picoagents.llm import AzureOpenAIChatCompletionClient
from picoagents.orchestration import AIOrchestrator
from picoagents.termination import MaxMessageTermination, TextMentionTermination
from picoagents.tools import (
    RESEARCH_TOOLS_AVAILABLE,
    RegexTool,
    ThinkTool,
)
from picoagents.types import OrchestrationResponse

# Import research tools if available
if RESEARCH_TOOLS_AVAILABLE:
    from picoagents.tools._research_tools import (
        GoogleSearchTool,
        WebFetchTool,
        YouTubeCaptionTool,
    )


def get_research_orchestrator():
    """Create AI-driven orchestrator with research-capable agents."""

    # Setup Azure OpenAI client
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")

    if not azure_endpoint or not api_key:
        raise ValueError(
            "Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables"
        )

    client = AzureOpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        azure_deployment=deployment,
    )

    # Check for Google Search API credentials
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")

    # Agent 1: Research Planner
    planner = Agent(
        name="planner",
        description="Research strategist who breaks down complex questions into research steps",
        instructions="""You are a research strategist. When given a research question:
        1. Analyze what information is needed
        2. Break it down into clear search steps
        3. Identify what sources would be most reliable (podcasts, papers, news, etc.)
        4. Suggest search queries and verification strategies

        Be specific about what to search for and why. Keep your plan concise (3-5 steps max).""",
        model_client=client,
        tools=[ThinkTool()],
    )

    # Agent 2: Information Gatherer (with search tools)
    gatherer_tools = [ThinkTool()]

    # Add Google Search if credentials available
    if RESEARCH_TOOLS_AVAILABLE and google_api_key and google_cse_id:
        gatherer_tools.append(GoogleSearchTool(api_key=google_api_key, cse_id=google_cse_id)) # type: ignore

    # Add web and YouTube tools if available
    if RESEARCH_TOOLS_AVAILABLE:
        gatherer_tools.extend([WebFetchTool(), YouTubeCaptionTool()]) # type: ignore

    gatherer = Agent(
        name="gatherer",
        description="Information gatherer with web search and content fetching capabilities",
        instructions="""You are an information gatherer. Execute search strategies:
        1. Use google_search to find relevant sources
        2. Use youtube_captions to get transcripts from YouTube videos
        3. Use web_fetch to retrieve content from web pages
        4. Extract key information and pass it to the analyzer

        Be systematic - search first, then fetch specific sources. Report what you found.""",
        model_client=client,
        tools=gatherer_tools, # type: ignore
    )

    # Agent 3: Content Analyzer (extracts specific info)
    analyzer = Agent(
        name="analyzer",
        description="Content analyst who extracts specific information from gathered sources",
        instructions="""You are a content analyst. Given raw content (transcripts, articles):
        1. Use regex_search to find specific mentions, quotes, or patterns
        2. Extract relevant passages that answer the research question
        3. Identify key quotes and attribute them properly
        4. Note any ambiguities or missing information

        Be precise - cite specific quotes when possible. Use regex for pattern matching.""",
        model_client=client,
        tools=[ThinkTool(), RegexTool()],
    )

    # Agent 4: Synthesizer (composes final answer)
    synthesizer = Agent(
        name="synthesizer",
        description="Research synthesizer who composes coherent answers from gathered evidence",
        instructions="""You are a research synthesizer. Given analyzed information:
        1. Compose a clear, factual answer to the original question
        2. Include specific quotes and attributions where relevant
        3. Note any limitations or uncertainties
        4. Organize information logically

        If the answer is complete and well-supported, end with: RESEARCH_COMPLETE
        If more information is needed, specify what's missing.""",
        model_client=client,
        tools=[ThinkTool()],
    )

    # Create termination conditions
    termination = MaxMessageTermination(max_messages=25) | TextMentionTermination(
        text="RESEARCH_COMPLETE"
    )

    # Create AI orchestrator - intelligently coordinates research workflow
    orchestrator = AIOrchestrator(
        agents=[planner, gatherer, analyzer, synthesizer],
        termination=termination,
        model_client=client,
        max_iterations=15,
    )

    return orchestrator


async def main():
    """Demonstrate AI-driven research team on a complex information gathering task."""

    orchestrator = get_research_orchestrator()

    # Example research task: Podcast + specific information extraction
    task = """Did Andrej Karpathy have a podcast interview with Dwarkesh Patel
    where he discussed Eureka Labs? If so, what did he say was the primary
    goal of Eureka Labs? Provide specific quotes if possible."""

    print("=" * 70)
    print("AI-DRIVEN RESEARCH TEAM")
    print("=" * 70)
    print(f"\nResearch Question:\n{task}\n")
    print("=" * 70)
    print("\n🔬 Research team is working...\n")

    # Run orchestration with streaming to see the research process
    async for item in orchestrator.run_stream(task, verbose=True):
        if isinstance(item, OrchestrationResponse):
            print("\n" + "=" * 70)
            print("RESEARCH RESULTS")
            print("=" * 70)
            print(f"\n{item.final_result}\n")
            print("=" * 70)
            print(f"Stop reason: {item.stop_message.content}")
            print(f"Total messages: {len(item.messages)}")
            print(f"Iterations: {len(item.pattern_metadata.get('selection_history', []))}")

            # Show AI orchestrator analytics
            metadata = item.pattern_metadata
            print(f"\n📊 Research Team Analytics:")
            print(
                f"   • Agents used: {metadata.get('unique_agents_selected', 0)}/{len(orchestrator.agents)}"
            )
            print(f"   • Agent diversity: {metadata.get('agent_diversity', 0):.1%}")
            print(
                f"   • Average confidence: {metadata.get('average_confidence', 0):.2f}"
            )

            if "selection_history" in metadata and metadata["selection_history"]:
                sequence = " → ".join([sel["agent"] for sel in metadata["selection_history"]])
                print(f"   • Workflow: {sequence}")

                # Show which agents did what
                agent_counts = {}
                for sel in metadata["selection_history"]:
                    agent_counts[sel["agent"]] = agent_counts.get(sel["agent"], 0) + 1
                print(f"   • Agent contributions:")
                for agent, count in sorted(agent_counts.items(), key=lambda x: -x[1]):
                    print(f"      - {agent}: {count} turns")


if __name__ == "__main__":
    print("\n⚠️  NOTE: This example requires:")
    print("   - AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
    print("   - GOOGLE_API_KEY and GOOGLE_CSE_ID (for web search)")
    print("   - Install: pip install 'picoagents[all]'\n")

    asyncio.run(main())

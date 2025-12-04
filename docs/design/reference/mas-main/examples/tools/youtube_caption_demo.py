#!/usr/bin/env python3
"""
Example demonstrating the YouTube caption extraction tool in picoagents.

This example shows how to use the YouTubeCaptionTool to extract and analyze
transcripts from YouTube videos.

Requirements:
- pip install picoagents[research]  # Installs youtube-transcript-api
- AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY environment variables

IMPORTANT NOTE:
This tool uses YouTube's unofficial transcript API which may occasionally fail due to:
- Rate limiting / bot detection by YouTube
- Regional restrictions on videos
- Videos without captions
- Network issues or API changes

If you encounter failures, try:
1. Waiting a few minutes and retrying
2. Using a different video
3. Running from a different network/location

Run with: python examples/tools/youtube_caption_demo.py
"""

import asyncio
import os

from picoagents import Agent
from picoagents.llm import AzureOpenAIChatCompletionClient
from picoagents.tools import YouTubeCaptionTool


async def demo_youtube_caption():
    """Demonstrate extracting and analyzing YouTube video transcripts."""
    print("\n" + "=" * 60)
    print("DEMO: YouTube Caption Extraction Tool")
    print("=" * 60)

    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")

    if not azure_endpoint or not api_key:
        print("⚠️  Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY to run this demo")
        return

    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # noqa

        print("✓ youtube-transcript-api is installed")
    except ImportError:
        print("⚠️  YouTube caption tool requires additional dependencies:")
        print("    pip install picoagents[research]")
        print("    or: pip install youtube-transcript-api")
        return

    client = AzureOpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        azure_deployment=deployment,
    )

    agent = Agent(
        name="video_analyst",
        description="Agent that analyzes YouTube video content from transcripts",
        instructions="""You are a helpful assistant that can extract and analyze YouTube video transcripts.
When given a YouTube URL, use the youtube_caption tool to get the transcript, then provide a helpful summary
or analysis based on what was requested.""",
        model_client=client,
        tools=[YouTubeCaptionTool()],
    )

    # Example 1: Basic transcript extraction
    print("\n--- Example 1: Extract and Summarize ---")
    task1 = "Get the transcript from this video: https://www.youtube.com/watch?v=dQw4w9WgXcQ and provide a brief summary of what it's about."

    print(f"\nTask: {task1}\n")
    response1 = await agent.run(task1)
    print(f"Agent: {response1.messages[-1].content}\n")

    # Example 2: Different URL format (youtu.be)
    print("\n--- Example 2: Short URL Format ---")
    task2 = "Extract the caption from https://youtu.be/dQw4w9WgXcQ and count how many times the word 'never' appears."

    print(f"\nTask: {task2}\n")
    response2 = await agent.run(task2)
    print(f"Agent: {response2.messages[-1].content}\n")


async def demo_direct_tool_use():
    """Demonstrate using the YouTube caption tool directly without an agent."""
    print("\n" + "=" * 60)
    print("DEMO: Direct Tool Usage (No Agent)")
    print("=" * 60)

    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # noqa

        print("✓ youtube-transcript-api is installed\n")
    except ImportError:
        print("⚠️  YouTube caption tool requires: pip install youtube-transcript-api")
        return

    tool = YouTubeCaptionTool()

    # Test with a YouTube video
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    print(f"Extracting captions from: {video_url}\n")

    result = await tool.execute({"url": video_url, "language": "en"})

    if result.success:
        print("✓ Caption extraction successful!")
        print(f"\nMetadata:")
        print(f"  - Video ID: {result.metadata.get('video_id')}")
        print(f"  - Language: {result.metadata.get('language')}")
        print(f"  - Length: {result.metadata.get('length')} characters")
        print(f"  - Segments: {result.metadata.get('segment_count')}")
        print(
            f"  - Available languages: {', '.join(result.metadata.get('available_languages', []))}"
        )

        print(f"\nTranscript preview (first 300 characters):")
        print(result.result[:300] + "...")
    else:
        print(f"✗ Caption extraction failed: {result.error}")


async def main():
    """Run all YouTube caption demos."""
    print("\n" + "=" * 60)
    print("PICOAGENTS YOUTUBE CAPTION TOOL DEMO")
    print("=" * 60)
    print("\nThis demo showcases the YouTube caption extraction tool:")
    print("  - Extract transcripts from YouTube videos")
    print("  - Support for multiple URL formats (youtube.com, youtu.be)")
    print("  - Multi-language caption support")
    print("  - Integration with agent workflows")

    # Run direct tool demo first
    await demo_direct_tool_use()

    # Then run agent-based demo
    await demo_youtube_caption()

    print("\n" + "=" * 60)
    print("ALL DEMOS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

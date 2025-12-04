"""
Day 2 Demo: Workflow with Design and Review Agents

This script demonstrates running the workflow with real AI agents
using Google's Gemini model.

To run this demo:
1. Set GOOGLE_API_KEY environment variable
2. Run: python examples/day2_demo.py

Without API key, it will fall back to stub mode.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path to import src module
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration import WorkflowEngine
from src.models import GoogleGeminiClient
from src.agents.design_agent import DesignAgent
from src.agents.review_agent import ReviewAgent


async def main():
    """Run workflow demo with agents."""
    # Check if API key is available
    api_key = os.getenv("GOOGLE_API_KEY")

    if api_key:
        print("✓ Google API key found - using real AI agents")
        print(f"  Using model: gemini-2.5-flash")
        print()

        # Create model client
        model_client = GoogleGeminiClient(
            model_name="gemini-2.5-flash",
            default_temperature=0.7,
        )

        # Create agents
        design_agent = DesignAgent(model_client)
        review_agent = ReviewAgent(model_client)

        # Create workflow with agents
        engine = WorkflowEngine(
            design_agent=design_agent,
            review_agent=review_agent,
        )

        print("Running workflow with AI agents...")
    else:
        print("⚠ No GOOGLE_API_KEY found - using stub mode")
        print("  Set GOOGLE_API_KEY to use real AI agents")
        print()

        # Create workflow without agents (stub mode)
        engine = WorkflowEngine()

        print("Running workflow in stub mode...")

    # Run the workflow
    context = await engine.run(
        ticket_id="DAY2-DEMO-001",
        dry_run=True,
    )

    # Print results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    if context.design:
        print("\nDesign Agent Output:")
        print(f"  Problem: {context.design.problem_understanding[:100]}...")
        print(f"  Approach: {context.design.proposed_approach[:100]}...")
        print(f"  Target Files: {len(context.design.target_files)} files")
        print(f"  Plan Steps: {len(context.design.step_by_step_plan)} steps")

    if context.review:
        print("\nReview Agent Output:")
        print(f"  Decision: {context.review.decision.upper()}")
        print(f"  Comments: {len(context.review.comments)} items")
        if context.review.comments:
            print(f"  First Comment: {context.review.comments[0]}")

    print(f"\nWorkflow Status: {'SUCCESS' if context.is_successful() else 'FAILED'}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

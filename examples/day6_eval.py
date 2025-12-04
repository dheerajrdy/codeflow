"""
Day 6: Evaluation harness demo.

Runs CodeFlow across multiple tickets (stub-friendly) and saves an evaluation
report to runs/eval_<timestamp>.json.
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env for API keys if present
load_dotenv()

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.eval import run_evaluation_suite  # noqa: E402


async def main():
    tickets = os.getenv("EVAL_TICKETS", "EVAL-1,EVAL-2").split(",")
    dry_run = os.getenv("EVAL_DRY_RUN", "true").lower() in ("1", "true", "yes")
    config_path = os.getenv("CODEFLOW_CONFIG")

    report = await run_evaluation_suite(
        tickets=[t.strip() for t in tickets if t.strip()],
        config_path=config_path,
        dry_run=dry_run,
    )

    print("\nEvaluation Summary")
    print("------------------")
    print(f"Tickets: {len(report['tickets'])}")
    print(f"Successes: {report['successes']}")
    print(f"Failures: {report['failures']}")
    print(f"Success rate: {report['success_rate']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())

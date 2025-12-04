#!/usr/bin/env python3
"""
Visualize Context Engineering Results

Generates comparison chart from existing comparison_data.json.
Run after context_engineering.py completes.

Usage: python visualize_results.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt


def main():
    """Load results and generate visualization."""

    # Load existing comparison data
    results_dir = Path(__file__).parent / "results"
    data_file = results_dir / "comparison_data.json"

    if not data_file.exists():
        print(f"❌ Error: {data_file} not found!")
        print("   Run context_engineering.py first to generate results.")
        return

    with open(data_file) as f:
        results = json.load(f)

    # Brand colors from CLAUDE.md
    PRIMARY_COLOR = "#4146DB"  # Primary blue (isolation - best strategy)
    SECONDARY_COLOR = "#323E50"  # Dark gray (baseline)
    GREEN_COLOR = "#10B981"  # Green (compaction)

    colors = {
        "baseline": SECONDARY_COLOR,
        "compaction": GREEN_COLOR,
        "isolation": PRIMARY_COLOR,
    }

    # Multi-line labels for readability
    strategy_labels = {
        "baseline": "Baseline\n(No Context\nEngineering)",
        "compaction": "Context\nCompaction",
        "isolation": "Context\nIsolation",
    }

    # Set style
    plt.style.use("default")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # LEFT: Total Token Usage (Bar Chart)
    strategies = []
    totals = []
    strategy_colors = []

    for key, data in results.items():
        strategies.append(strategy_labels[key])
        totals.append(data["summary"]["cumulative_total_tokens"])
        strategy_colors.append(colors[key])

    bars = ax1.barh(
        strategies,
        totals,
        color=strategy_colors,
        alpha=0.85,
        edgecolor=SECONDARY_COLOR,
        linewidth=2,
    )

    # Add value labels at end of bars
    for bar, total in zip(bars, totals):
        width = bar.get_width()
        ax1.text(
            width + max(totals) * 0.02,
            bar.get_y() + bar.get_height() / 2.0,
            f"{int(total):,}",
            ha="left",
            va="center",
            fontsize=20,
            fontweight="bold",
            color=SECONDARY_COLOR,
        )

    ax1.set_xlabel("Total Tokens", fontsize=20, fontweight="bold", color=SECONDARY_COLOR)
    ax1.set_title(
        "Total Token Usage", fontsize=22, fontweight="bold", color=SECONDARY_COLOR, pad=20
    )
    ax1.tick_params(axis="both", which="major", labelsize=17, colors=SECONDARY_COLOR)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_color(SECONDARY_COLOR)
    ax1.spines["bottom"].set_color(SECONDARY_COLOR)
    ax1.grid(axis="x", alpha=0.2, linestyle="--")

    # RIGHT: Token Growth Over Time (Line Chart)
    for key, data in results.items():
        history = data["history"]
        model_calls = [h for h in history if h["operation_type"] == "model_call"]

        if model_calls:
            steps = [h["operation"] for h in model_calls]
            cumulative = [h["cumulative_total"] for h in model_calls]
            ax2.plot(
                steps,
                cumulative,
                marker="o",
                linewidth=3,
                color=colors[key],
                label=data["name"],
                markersize=8,
                alpha=0.9,
            )

            # Add LARGER endpoint label
            final_tokens = cumulative[-1]
            ax2.text(
                steps[-1] + 0.3,
                final_tokens,
                f"{int(final_tokens/1000)}K",
                fontsize=22,
                fontweight="bold",
                color=colors[key],
                va="center",
            )

    ax2.set_xlabel("Model Calls", fontsize=20, fontweight="bold", color=SECONDARY_COLOR)
    ax2.set_ylabel("Cumulative Tokens", fontsize=20, fontweight="bold", color=SECONDARY_COLOR)
    ax2.set_title(
        "Token Growth Over Time",
        fontsize=22,
        fontweight="bold",
        color=SECONDARY_COLOR,
        pad=20,
    )
    ax2.legend(fontsize=15, loc="upper left", frameon=True, fancybox=True, shadow=False)
    ax2.tick_params(axis="both", which="major", labelsize=17, colors=SECONDARY_COLOR)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.spines["left"].set_color(SECONDARY_COLOR)
    ax2.spines["bottom"].set_color(SECONDARY_COLOR)
    ax2.grid(True, alpha=0.2, linestyle="--")

    plt.tight_layout()
    output_file = results_dir / "context_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()

    print(f"✓ Visualization saved: {output_file}")


if __name__ == "__main__":
    main()

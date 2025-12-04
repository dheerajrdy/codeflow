# Multi-Agent Evaluation Suite

Comprehensive evaluation framework for comparing direct models, single agents, and multi-agent systems.

## Quick Start

### One Script, Two Modes

The `comprehensive-evaluation.py` script has everything integrated:

```bash
# Quick test (3 tasks, 4 configs, ~1 minute) - RECOMMENDED FIRST
python comprehensive-evaluation.py quick

# Full evaluation (10 tasks, 4 configs, ~5-10 minutes)
python comprehensive-evaluation.py full
# or simply:
python comprehensive-evaluation.py
```

**Auto-generates:**
- CSV results with scores + **reasoning** (WHY scores are what they are)
- Visualization charts (performance vs efficiency)
- Summary statistics

**Results:**
- `quick_results/quick_results.csv` + `evaluation_results.png`
- `comprehensive_results/comprehensive_results.csv` + `evaluation_results.png`

## What We're Testing

### Configurations

1. **Direct-Model** - Baseline (no agent wrapper)
2. **Single-Agent-Tools** - Agent with tools (Calculator, DateTime, Think)
3. **Multi-Agent-RoundRobin** - Fixed-order team (Planner → Solver → Reviewer)
4. **Multi-Agent-AI** - Dynamic orchestration (AI selects speakers)

### Task Categories

**Quick Test (3 tasks):**
- Math word problem
- Calculator usage
- Logic puzzle

**Comprehensive (10 tasks across 4 categories):**
- **Simple Reasoning** (3 tasks) - Math, logic, comprehension
- **Tool-Heavy** (3 tasks) - Real-time data, calculations, date operations
- **Complex Planning** (2 tasks) - Multi-constraint optimization
- **Verification** (2 tasks) - Fact-checking, argument analysis

### Evaluation Metrics

- **Overall Score** (0-10) - Composite quality assessment
- **Accuracy** - Correctness of response
- **Completeness** - Thoroughness of answer
- **Helpfulness** - Practical value
- **Clarity** - Communication quality
- **Tokens** - Resource consumption (input + output)
- **Duration** - Wall-clock time (ms)
- **LLM Calls** - API invocations

## Interpreting Results

### Performance vs Efficiency

The key insight: **Multi-agent systems should justify their overhead.**

**Example from quick test:**
```
Configuration    Score    Tokens    Efficiency (pts/1K tok)
Direct-Model     7.4/10   156       47.5
Multi-Agent-RR   7.2/10   2157      3.4
```

**Teaching moment:** Multi-agent uses 14x more tokens but scores lower on simple tasks!

### When Multi-Agent Should Win

Multi-agent systems should show advantages on:
- **Complex planning** - Multi-step decomposition
- **Tool-heavy tasks** - Specialized tool usage
- **Verification tasks** - Critique and review cycles
- **Multi-constraint** - Balancing competing requirements

### Task Breakdown Analysis

Look for patterns:
- Which tasks benefit from multi-agent coordination?
- Where does orchestration overhead hurt performance?
- Do specialized agents outperform generalists?

## Tuning Configurations

### Common Adjustments

**If teams timeout:**
```python
# Increase message limits
termination=MaxMessageTermination(max_messages=50)  # was 30

# Increase iterations
max_iterations=15  # was 10
```

**If quality is low:**
```python
# Improve agent instructions
# Add more specific tool guidance
# Adjust evaluation criteria
```

**If costs are too high:**
```python
# Use fewer evaluation runs
# Reduce task suite size
# Skip expensive composite judges
```

## Bug Fix Applied

This evaluation suite discovered and fixed a critical PicoAgents bug:

**Issue:** `LLMEvalJudge` was importing from wrong `BaseEvalJudge` class
**Fix:** Changed `from .._base import BaseEvalJudge` → `from ._base import BaseEvalJudge`
**Location:** `picoagents/src/picoagents/eval/judges/_llm.py:14`

## Next Steps

1. **Run quick test** - Validate setup and tune parameters
2. **Analyze results** - Look for patterns and insights
3. **Iterate configs** - Adjust based on findings
4. **Run comprehensive** - Full evaluation for book/paper
5. **Update chapter** - Integrate results and visualizations

## File Structure

```
evaluation/
├── README.md                           # This file
├── comprehensive-evaluation.py         # Main script (quick + full modes, auto-viz)
├── agent-evaluation.py                 # Original example (educational reference)
├── reference-based-evaluation.py       # Judge type demonstrations
├── quick_results/
│   ├── quick_results.csv               # Scores + reasoning
│   └── evaluation_results.png          # Auto-generated charts
└── comprehensive_results/
    ├── comprehensive_results.csv       # Full dataset + reasoning
    └── evaluation_results.png          # Auto-generated charts
```

## Requirements

- Azure OpenAI credentials (set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`)
- Optional: Google Search API (set `GOOGLE_API_KEY`, `GOOGLE_CSE_ID`) for web search tasks
- Python packages: `picoagents`, `pandas`, `matplotlib`

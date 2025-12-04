# Context Engineering Examples

This directory demonstrates three strategies for managing LLM context growth in multi-agent systems.

## Quick Start

```bash
# Run all three strategies and compare results
python context_strategies.py

# Regenerate visualization from existing results (optional)
python visualize_results.py
```

## Files

- **`context_strategies.py`** - Single file with all three strategy implementations, token tracking, and visualization
- **`mock_tools.py`** - Reusable mock tools with realistic variance for reproducible testing
- **`token_tracking.py`** - Token tracking middleware (imported by context_strategies.py)
- **`visualize_results.py`** - Optional: regenerate charts from existing comparison_data.json
- **`results/`** - Output directory for comparison_data.json and context_comparison.png

## Three Strategies

### 1. Baseline (No Context Management)
- All messages accumulate in context window
- No trimming or isolation
- **Result:** ~21,633 tokens

### 2. Context Compaction
- Automatic trimming of old messages via middleware
- Keeps system messages + last 5 conversation turns
- **Result:** ~7,276 tokens (66% reduction)

### 3. Context Isolation
- Hierarchical agents with isolated contexts
- Specialist handles research, coordinator sees only summaries
- **Result:** ~5,892 tokens (73% reduction)

## Understanding the Results

The visualization (`results/context_comparison.png`) shows:

- **Left panel:** Total token usage comparison across all three strategies
- **Right panel:** Token growth over time (cumulative tokens vs model calls)

Context Isolation provides the best token savings by preventing context explosion through architectural design rather than reactive trimming.

## Implementation Details

All three strategies use the same:
- Model: gpt-4.1-mini (Azure OpenAI)
- Task: Research 3 AI/ML companies (company details, funding, metrics)
- Tools: search, company_details, funding_info, traction_metrics, analyze, report

The only difference is the context management strategy applied.

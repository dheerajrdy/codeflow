# YC Agent Analysis Workflow

Production-ready data analysis demonstrating PicoAgents patterns.

## Key Insights

• **234/5,000+ YC companies (4.7%) now build AI agents** (2024 data)
• **Growth**: From 5 companies (2020) to 234 companies (2024) - 47x increase
• **Top domains**: Productivity (89), Health (34), Finance (28)
• **Cost efficiency**: 90% reduction via keyword pre-filtering

## Engineering Patterns

**Two-stage filtering**: Keywords → AI classification saves $4+ per run
**Structured output**: Zero hallucination with Pydantic schemas
**Disk checkpoints**: Resume processing after interruptions
**Independent testing**: Each step unit-testable

## Quick Start

```bash
# Set credentials
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-key"

# Run analysis
python workflow.py

# Run tests
python test_workflow.py
```

## Files

- `models.py` - Pydantic schemas for type safety
- `steps.py` - Individual workflow functions (testable)
- `workflow.py` - Main orchestration
- `test_workflow.py` - Unit tests for each component
- `data/` - Cache directory (gitignored)

Generated report: `./yc_analysis/data/analysis.md`
# OpenTelemetry Integration Example

This example demonstrates automatic telemetry collection in PicoAgents using OpenTelemetry.

## What Gets Instrumented?

When you enable OpenTelemetry, PicoAgents automatically collects:

- **Traces**: Spans for agent operations, LLM calls, and tool executions
- **Metrics**: Token usage histograms and operation duration
- **Semantic Conventions**: Follows OpenTelemetry Gen-AI standards

## Quick Start

### 1. Install Dependencies

```bash
# From the repository root
cd picoagents
pip install -e ".[otel]"
```

### 2. Start Jaeger

```bash
# From the repository root
cd examples/otel
docker-compose up -d
```

This starts Jaeger on:
- UI: http://localhost:16686
- OTLP endpoint: http://localhost:4318

### 3. Set Environment Variables

```bash
export PICOAGENTS_ENABLE_OTEL=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=picoagents-example
export OPENAI_API_KEY=your-api-key
```

### 4. Run the Example

```bash
python agent_with_telemetry.py
```

### 5. View Traces in Jaeger

1. Open http://localhost:16686
2. Select service: `picoagents-example`
3. Click "Find Traces"
4. Explore the trace hierarchy

## What You'll See

### Trace Hierarchy
```
agent weather_assistant
├─ chat gpt-4o-mini
│  └─ Attributes: gen_ai.usage.input_tokens, gen_ai.usage.output_tokens
├─ tool get_weather
│  └─ Attributes: gen_ai.tool.name, gen_ai.tool.success
└─ chat gpt-4o-mini
   └─ Final response with usage stats
```

### Metrics (in Jaeger)
- `gen_ai.client.token.usage`: Token consumption histograms
- `gen_ai.client.operation.duration`: Operation latency

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PICOAGENTS_ENABLE_OTEL` | `false` | Enable OpenTelemetry |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318` | OTLP endpoint URL |
| `OTEL_SERVICE_NAME` | `picoagents` | Service name for traces |

## Cleanup

```bash
docker-compose down
```

## Using with Other Backends

PicoAgents works with any OTLP-compatible backend:

### Datadog
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=https://api.datadoghq.com
export DD_API_KEY=your-datadog-api-key
```

### Honeycomb
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io
export HONEYCOMB_API_KEY=your-api-key
```

### New Relic
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp.nr-data.net
export NEW_RELIC_LICENSE_KEY=your-license-key
```

## Learn More

- [OpenTelemetry Gen-AI Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [PicoAgents Middleware](../../picoagents/src/picoagents/_middleware.py)

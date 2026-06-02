# Architecture

`ops-copilot` keeps the operational path explicit: users ask for an investigation, the graph asks a model which reviewed tool to call, and tool output is redacted before it returns to the model, stream, audit log, or report.

## Data Flow

```text
User or UI
  |
  v
FastAPI server or direct Python caller
  |
  v
InvestigationGraph
  |
  +--> LLM selects a registered tool
  |      |
  |      v
  |    ToolRegistry
  |      |
  |      v
  |    ShellTool or custom RemoteTool
  |      |
  |      v
  |    SSHClient executes reviewed command
  |      |
  |      v
  |    Redaction and sanitization
  |
  +--> Stream events, audit log, incident report
```

## Main Components

- `InvestigationGraph`: LangGraph-based investigation loop and streaming event source.
- `ToolRegistry`: loads reviewed YAML tools and injectable Python tools.
- `ShellTool`: renders command templates with typed and validated parameters.
- `CommandPolicy`: blocks obvious destructive command families unless explicitly allowed.
- `SSHClient`: executes reviewed commands on operator-controlled hosts.
- `redact_secrets`: removes common token and secret shapes from outputs.
- `JsonlAuditLog`: stores redacted event evidence for later review.
- `IncidentReport`: summarizes redacted investigation evidence.
- `create_app`: optional FastAPI JSON/SSE API surface.

## Safety Boundaries

- The model can only request registered tools.
- YAML and custom tools are privileged code and must be reviewed before deployment.
- String parameters are constrained by `allowed_values`, `pattern`, or a conservative default validator.
- Tool output is redacted before it is sent back to model-facing or user-facing surfaces.
- The API server should use `OPS_COPILOT_API_KEY` when exposed over a network.

See `docs/security-model.md` and `docs/threat-model.md` for the full safety model.

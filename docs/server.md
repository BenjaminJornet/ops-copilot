# Server Integration

The optional server extra exposes a small FastAPI application with JSON and SSE endpoints.

## Install server dependencies

```bash
uv add 'ops-copilot[server]'
```

## Endpoints

- `POST /investigate`
- `POST /investigate/stream`

If `OPS_COPILOT_API_KEY` is set, requests must include `X-API-Key`.

## Request shape

```json
{
  "message": "The API is slow. Investigate the host.",
  "images": []
}
```

## SSE events

The streaming endpoint emits events with these names:

- `token`
- `tool_start`
- `tool_end`
- `error`
- `done`

Example event payload:

```json
{
  "tool": "disk_usage",
  "output": "Filesystem Size Used Avail Use% Mounted on",
  "step_id": "disk_usage:..."
}
```

## Minimal app factory

```python
from ops_copilot.server import create_app


def graph_factory():
    return graph


app = create_app(graph_factory)
```

Run with:

```bash
uvicorn app:app --host 127.0.0.1 --port 8000
```

Do not expose the server publicly without authentication and a reviewed tool set.

## Summary

## Safety checklist

- [ ] Added or updated tests.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run pytest` passes.
- [ ] No real hostnames, private IPs, credentials, tokens, or internal service names were added.
- [ ] Tool output is redacted before it reaches the LLM or SSE stream.
- [ ] New shell commands are narrow, documented, and non-destructive.
- [ ] Security assumptions are documented when behavior changes.

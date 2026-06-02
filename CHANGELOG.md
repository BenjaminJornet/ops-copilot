# Changelog

## Unreleased

## 0.1.8

- Replaced platform-specific repository documentation with agent-agnostic maintenance guidance.
- Added architecture documentation and a terminal demo SVG preview.
- Added a recorded asciinema terminal demo and deterministic recording script.
- Added a `bad-env-var` incident fixture with replay CLI coverage.
- Updated GitHub Actions to newer resolvable major versions where available.

## 0.1.7

- Added packaged `ops-copilot review` and `ops-copilot replay` maintainer commands.
- Added ecosystem smoke workflow for the three-repository local demo.
- Added STRIDE-style threat model documentation and sharper README demo/safety sections.
- Added `httpx2` for Starlette TestClient and made pytest warnings fail by default, with a targeted upstream LangChain Python 3.14 exception.

## 0.1.6

## 0.1.5

- Added fixture replay demo, agent maintenance guide, toolpack review, structured incident reports, and in-memory sessions.

## 0.1.4

- Added shell command policy checks, dry-run support, audit logging, and incident fixtures.

## 0.1.3

- Added reviewed Linux, systemd, and Docker example toolpacks.
- Added toolpack documentation and tests.
- Added FastAPI JSON and SSE server smoke tests.

## 0.1.2

- Added maintainer documentation, security policy, release process, and issue/PR templates.
- Added security model, tool-writing, server, and maintenance-workflow documentation.
- Added local demo and custom tool examples.
- Added build and manual publish workflows.
- Added PyPI metadata, badges, and typed package marker.
- Added basic shell parameter validation controls for safer YAML tools.

## 0.1.0

Initial public release.

- Added SSH client with lazy reconnect and command timeout handling.
- Added YAML-driven shell tools and injectable custom tool registry.
- Added LangGraph investigation loop with streaming events.
- Added FastAPI SSE integration helper.
- Added input/output sanitization and secret redaction.
- Added examples, tests, and CI.

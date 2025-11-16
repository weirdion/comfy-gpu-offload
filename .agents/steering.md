# comfy-gpu-offload – Engineering & Coding Guidelines

This document defines engineering standards for the `comfy-gpu-offload` project. All code and documentation changes in this repo should follow these guidelines.

---

## Languages, Runtime, and Tooling

- **Primary language**: Python 3.11+ (or the project’s configured minimum).
- **Project layout**:
  - Use a modern packaging layout: `pyproject.toml` with a `src/`-based package.
  - Package name: `comfy_gpu_offload` (under `src/comfy_gpu_offload/`).

- **Recommended tools** (configure in `pyproject.toml` as appropriate):
  - Formatting: `black` or `ruff format`.
  - Linting: `ruff`.
  - Type checking: `mypy` (or `pyright` if already chosen).
  - Testing: `pytest`.
  - Security scanning: `bandit` (or similar) as a pre-release check.

Always align new configuration with existing `pyproject.toml` once it exists.

---

## Architecture & Module Structure

Aim for a small, well-organized Python package with clear separation of concerns:

- `src/comfy_gpu_offload/config/…`
  - Configuration models, environment variable loading, and validation.
- `src/comfy_gpu_offload/api/runpod_client.py`
  - Typed client for RunPod HTTP API (submit, poll, fetch results).
- `src/comfy_gpu_offload/io/…`
  - Image/video encoding/decoding, temp file management, cleanup.
- `src/comfy_gpu_offload/workflow/…`
  - Workflow (de)serialization, transformations, and payload building for RunPod.
- `src/comfy_gpu_offload/nodes/…`
  - ComfyUI node definitions, kept thin; delegate heavy logic to other modules.
- `tests/…`
  - Unit and integration tests mirroring the package structure.

Avoid “god modules.” Each module should have a single, clear purpose.

---

## Typing & Interfaces

- Use **PEP 484** type hints for all public functions, methods, and module-level variables.
- Prefer explicit `TypedDict`, `dataclass`, or `pydantic`-style models (if introduced) for structured data, instead of raw `dict[str, Any]`.
- Avoid `Any` unless absolutely necessary; if used, localize it and document why.
- Functions should have clear, minimal parameter lists. Group related inputs into typed objects when it makes interfaces clearer.

Example (pattern, not exact requirement):

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class RunpodConfig:
    api_key: str
    endpoint_id: str
    base_url: str
    timeout_seconds: float
    verify_tls: bool
```

---

## Configuration & Secrets

- No secrets (API keys, tokens, endpoint URLs with secrets) may be committed to the repo.
- Configuration should come from:
  - Environment variables (e.g., `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_ID`, `RUNPOD_BASE_URL`).
  - Optionally a `.env` file loaded via `python-dotenv`, with `.env` in `.gitignore`.

- Provide a small, typed config layer that:
  - Validates required values at startup or first use.
  - Provides clear, actionable error messages when config is missing/invalid.
  - Never logs secrets; if you must mention config values in logs, redact them.

---

## HTTP & RunPod API

- Use `requests` or another well-established HTTP client.
- Always:
  - Use `https://` endpoints.
  - Enable TLS verification (do not disable `verify` unless strictly necessary and documented).
  - Use timeouts for all HTTP calls (no unbounded blocking).

- Implement a small client abstraction:
  - Functions or a class that encapsulates API calls (`submit_job`, `get_job_status`, `get_result`).
  - Handle known error cases (4xx, 5xx, network errors) and wrap them in project-specific exceptions.
  - Implement retry with backoff for idempotent operations (e.g., status polling), with max attempts and a total timeout.

Do not expose raw HTTP details to ComfyUI nodes; keep them behind the client interface.

---

## File I/O, Images, and Artifacts

- Prefer working in dedicated, project-specific temporary directories.
- Use secure file permissions where appropriate (e.g., `0o600` for outputs containing user data).
- Clean up temporary files/directories deterministically, even on failure paths where feasible.
- Keep image/video encode/decode operations in dedicated helper functions.
- Use well-known libraries for media operations (e.g., Pillow) instead of ad-hoc binary manipulation.

Never leave large artifacts lying around outside of well-defined directories.

---

## ComfyUI Node Design

- Node files should:
  - Be located in a clearly named module under `src/comfy_gpu_offload/nodes/`.
  - Define `NODE_CLASS_MAPPINGS` and any relevant metadata.
  - Keep logic thin: perform basic argument handling and delegate to internal services.

- Node behavior:
  - Provide a simple “Use RunPod” boolean/toggle where relevant.
  - Fail fast and clearly when misconfigured (e.g., missing API key).
  - Surface understandable error messages to the user, without leaking secrets.

- Do **not**:
  - Patch or rely on ComfyUI internals outside of public/custom node APIs.
  - Introduce global side effects at import time (e.g., starting background threads).

---

## Logging, Errors, and Observability

- Use Python’s `logging` module, not `print`, for diagnostics.
- Log at appropriate levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
- Never log:
  - API keys or tokens.
  - Entire request/response bodies that may contain prompts or images.

- Prefer:
  - Clear, user-facing error messages that summarize the failure.
  - More detailed, internal logs that aid debugging (without leaking secrets).

Define and use project-specific exception types where helpful (e.g., `RunpodApiError`, `ConfigError`).

---

## Testing Strategy

- Use `pytest` with a conventional layout: `tests/` mirroring `src/`.
- For new modules, add unit tests that cover:
  - Happy paths.
  - Error handling and edge cases.
  - Input validation and config validation.

- For HTTP/RunPod interactions:
  - Mock external HTTP calls (e.g., via `responses` or `requests-mock`).
  - Do not hit real RunPod endpoints in automated tests.

- For I/O and workflows:
  - Test encode/decode helpers with small fixtures.
  - Test workflow transformation functions with minimal example workflows.

Aim for meaningful coverage over raw coverage percentage; prioritize testing public interfaces and critical logic.

---

## Style & Readability

- Follow PEP 8, except where the configured formatter (e.g., `black`) differs.
- Use descriptive, non-abbreviated names for variables, functions, and classes.
- Avoid one-letter variable names except for small, obvious scopes (e.g., `for i in range(...)`).
- Avoid inline comments explaining *what* obvious code does; comment to explain *why* when needed.
- Prefer early returns over deeply nested `if` chains.

---

## Dependencies

- Keep the dependency set minimal and focused.
- Before adding a new dependency:
  - Check whether the standard library or existing dependencies already cover the need.
  - Consider security, maintenance, and ecosystem reputation.

- All dependencies must be pinned with compatible version ranges in `pyproject.toml`.

---

## Documentation

- Maintain a clear `README` at the repo root:
  - Project overview (aligned with `.agents/vision.md`).
  - Installation and configuration.
  - Basic usage and examples.

- Update docs when behavior, configuration, or public APIs change.
- Prefer short, focused docs over long, unstructured text.

---

## Security Checklist (Per Change)

Before considering a change “done,” confirm:

- No secrets are added to code, tests, or fixtures.
- No sensitive data is logged or written in an unsafe way.
- External calls validate TLS and use timeouts.
- Inputs are validated where they cross trust boundaries (e.g., user-facing node inputs, environment variables, HTTP responses).

---

Following these guidelines should keep `comfy-gpu-offload` small, secure, maintainable, and pleasant to work on. New contributors and LLM agents should treat this file, along with `.agents/vision.md` and `.agents/context/ongoing.md`, as the primary source of truth for “how we build things here.”


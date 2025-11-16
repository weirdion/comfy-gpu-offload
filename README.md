# comfy-gpu-offload

ComfyUI custom nodes for offloading GPU-heavy workloads to RunPod serverless endpoints while keeping ComfyUI running locally for workflow authoring and preview.

## Status

Project scaffolding is in place (Python 3.13, uv, src/ layout, basic tooling config). Implementation of config, RunPod client, workflow utilities, and nodes is pending.

## Developing

```bash
# create env (uv)
uv venv
source .venv/bin/activate

# install project + dev tools
uv pip install -e .[dev]
```

Run checks:

```bash
ruff check .
ruff format .
mypy .
pytest
```

## Testing in ComfyUI

Clone or symlink this repo into `ComfyUI/custom_nodes/` to test nodes once implemented.

## Security

- No secrets committed; use environment variables (e.g., `RUNPOD_API_KEY`).
- TLS verification and request timeouts are required for all HTTP calls.
- Avoid logging sensitive payloads or prompts.


# comfy-gpu-offload

ComfyUI custom nodes for offloading GPU-heavy workloads to RunPod serverless endpoints while keeping ComfyUI running locally for workflow authoring and preview.

## Status

Project scaffolding is in place (Python 3.13, uv, src/ layout, basic tooling config). Implementation of config, RunPod client, workflow utilities, and nodes is pending.

## Developing

```bash
make setup        # creates/updates .venv with uv and installs deps
source .venv/bin/activate
```

Common tasks (via Makefile):

```bash
make fix          # format + autofix lint
make checks       # lint + format-check + typecheck + tests + bandit
# optional (requires snyk CLI + SNYK_TOKEN): make snyk
```

## Quick Start (ComfyUI)

Clone or symlink this repo into `ComfyUI/custom_nodes/` to test nodes:

```bash
git clone https://github.com/your-org/comfy-gpu-offload.git
ln -s $(pwd)/comfy-gpu-offload ~/workspace/ai/ComfyUI/custom_nodes/comfy-gpu-offload
```

Start ComfyUI and the node will appear under the “RunPod” category.

## Configuration

Set environment variables (e.g., in your shell or a local `.env` not committed):

- `RUNPOD_API_KEY` (required, secret)
- `RUNPOD_ENDPOINT_ID` (required)
- Optional:
  - `RUNPOD_BASE_URL` (default `https://api.runpod.ai`, must be HTTPS)
  - `RUNPOD_REQUEST_TIMEOUT` (seconds, default 30)
  - `RUNPOD_VERIFY_TLS` (default true)
  - `RUNPOD_POLL_INTERVAL` (seconds, default 3)
  - `RUNPOD_MAX_POLL_DURATION` (seconds, default 900)

## Security

- No secrets committed; use environment variables (e.g., `RUNPOD_API_KEY`).
- TLS verification and request timeouts are required for all HTTP calls.
- Avoid logging sensitive payloads or prompts.
- RunPod base URL must be HTTPS.
- Security practices and checklist: see `SECURITY.md`.

## Architecture (high level)

- `config`: typed env-driven config with validation and HTTPS enforcement.
- `api`: RunPod client (submit/status/cancel/poll) with timeouts and TLS verification.
- `workflow`: payload-building helpers with input validation.
- `io`: temp dir/file management with restricted permissions; image base64 helpers.
- `nodes`: ComfyUI node(s) wiring UI inputs to payload build + RunPod client.

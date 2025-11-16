# Ongoing Tasks – comfy-gpu-offload

1. ✅ Define clear project boundaries and data flow for the RunPod remote-execution node (local ComfyUI graph → RunPod serverless endpoint → results back into ComfyUI).
2. ✅ Scaffold the Python package and tooling for this repo (`pyproject.toml`, `src/comfy_gpu_offload/`, `.gitignore`) with formatting, linting, and type checking (e.g., `ruff`/`black`, `mypy` or `pyright`).
3. ✅ Establish configuration and secrets management: choose environment variable names (e.g., `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_ID`), optional `.env` loading, and a typed config object with validation and safe defaults.
4. ✅ Implement a typed RunPod API client module (submit job, poll status, fetch artifacts) with robust error handling, retries/backoff, and no logging of secrets or sensitive payloads.
5. ✅ Implement secure filesystem and I/O utilities for images/videos (temp directory management, strict file permissions, encoding/decoding helpers, deterministic cleanup).
6. ✅ Implement workflow serialization/deserialization utilities to translate between ComfyUI workflows and the JSON payload expected by the RunPod endpoint (including optional manual JSON override for debugging).
7. Implement the ComfyUI custom node(s) in this package (node classes, `NODE_CLASS_MAPPINGS`, inputs/outputs, “Use RunPod” toggle) that call the RunPod client and workflow utilities while keeping node code thin.
8. Implement progress reporting and cancellation support (polling loop with progress updates, timeouts, cancellation hooks) mapped cleanly into ComfyUI’s UI/UX patterns.
9. Harden security and privacy end-to-end: validate all user inputs, enforce HTTPS/TLS verification, avoid leaking prompts or URLs in logs, and ensure temporary data and downloaded artifacts are cleaned up securely.
10. Add a comprehensive automated test suite (`pytest`) covering config, API client (with mocked HTTP), workflow conversion, and I/O utilities, plus static analysis (`mypy` and `bandit` or similar).
11. Add developer and user documentation: project README, architecture overview (aligned with `vision.md`), configuration reference, example workflows, and instructions for cloning/symlinking into `ComfyUI/custom_nodes/` for local testing.
12. Prepare for initial release: choose and add license (MIT as recommended), define versioning strategy, update metadata for ComfyUI Manager compatibility, and create a minimal changelog for future iterations.

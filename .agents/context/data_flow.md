# comfy-gpu-offload – System Boundaries and Data Flow

## System Boundaries

- **In-scope (this repo)**
  - Python package `comfy_gpu_offload` with ComfyUI custom node(s).
  - RunPod client wrapper (submit job, poll status, fetch results/artifacts).
  - Workflow serialization/translation helpers and media I/O utilities.
  - Local filesystem handling for temp data and returned artifacts.

- **Out-of-scope**
  - Managing RunPod endpoints (provisioning, scaling, or billing).
  - Modifying ComfyUI core; only use the custom node interface.
  - Long-term artifact storage or CDN/S3 uploads (future enhancement only).
  - Training/fine-tuning models; assume models are available to the endpoint.

## Trust & Security Boundaries

- **Local host (trusted)**
  - ComfyUI UI and node execution environment.
  - Local filesystem for temp data; ensure strict permissions and cleanup.

- **RunPod API (external/untrusted)**
  - All HTTP traffic must use TLS with verification and call-level timeouts.
  - Never log secrets (API key, endpoint IDs) or full prompts/payloads.
  - Treat all responses as untrusted; validate and handle errors explicitly.

## Data Flow (happy path)

1. **User config**: API key, endpoint ID, base URL loaded from env (or `.env`), validated in a typed config object.
2. **ComfyUI workflow**: User builds/loads a graph locally; the custom node exposes a “Use RunPod” toggle and relevant settings.
3. **Payload build**: Node delegates to workflow utilities to serialize the graph/payload for RunPod, optionally merging manual overrides.
4. **Submission**: RunPod client sends the payload over HTTPS with timeouts; secrets stay in headers, never logged.
5. **Polling**: Client polls job status with bounded retries/backoff; supports cancellation/timeouts and surfaces progress to the node.
6. **Result fetch**: On completion, client fetches artifacts (images/video/JSON); validates content type/size and paths.
7. **Local handling**: I/O helpers store artifacts in temp dirs with restrictive permissions; node returns outputs into ComfyUI for preview/save.
8. **Cleanup**: Temp files/directories are cleaned deterministically after use; errors still attempt safe cleanup.

## Failure/Edge Considerations

- Invalid/missing config: Fail fast with actionable error messages (no secret leakage).
- Network/API errors: Use retries for idempotent calls; surface concise, user-safe errors.
- Large artifacts: Prefer streamed download to temp files; avoid loading entire binaries into memory when possible.
- Cancellation: Provide a path to stop polling and respect ComfyUI cancellation semantics if available.

## Data Types (canonical)

- **Inputs**: text prompts, workflow JSON, image/latent inputs, numeric params.
- **Outputs**: images/video artifacts, logs/status metadata, potentially workflow JSON echoes.
- **Secrets**: RunPod API key (mandatory), endpoint ID (non-secret but treated as sensitive), base URL (non-secret).

## Integration Notes

- Package remains an independent repo; clone/symlink into `ComfyUI/custom_nodes/` for testing.
- Keep node surface stable and minimal; push complexity into internal modules.
- Default to local execution behavior when “Use RunPod” is off; avoid breaking local-only workflows.


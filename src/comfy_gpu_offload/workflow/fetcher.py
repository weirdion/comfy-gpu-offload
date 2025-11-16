"""Fetch workflow JSON from a URL (e.g., ComfyUI API export)."""

import json
from typing import Any, Mapping
from urllib.parse import urlparse

import requests
from requests import Response
from requests.exceptions import RequestException

from comfy_gpu_offload.workflow.loader import DEFAULT_MAX_PAYLOAD_BYTES, WorkflowLoadError
from comfy_gpu_offload.workflow.payload import RunpodInputPayload


def fetch_workflow_from_url(
    url: str,
    *,
    timeout_seconds: float = 10.0,
    verify_tls: bool = True,
    max_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
) -> Mapping[str, Any]:
    """Fetch a workflow JSON document from a URL with validation and size guard."""
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"}:
        raise WorkflowLoadError("workflow_url must use http or https")
    if parsed.scheme == "http" and verify_tls:
        # We allow http only if caller disables verification explicitly.
        raise WorkflowLoadError("workflow_url must be https when verify_tls is enabled")

    try:
        resp: Response = requests.get(url, timeout=timeout_seconds, verify=verify_tls)
    except RequestException as exc:
        raise WorkflowLoadError(f"Failed to fetch workflow from URL: {exc}") from exc

    if resp.status_code >= 400:
        raise WorkflowLoadError(f"Workflow URL returned HTTP {resp.status_code}")

    raw = resp.content
    if len(raw) > max_bytes:
        raise WorkflowLoadError(
            f"Workflow payload too large ({len(raw)} bytes), limit {max_bytes} bytes"
        )

    try:
        parsed_json = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WorkflowLoadError(f"Invalid JSON from workflow_url: {exc}") from exc

    if not isinstance(parsed_json, Mapping):
        raise WorkflowLoadError("workflow_url must return a JSON object")
    if not parsed_json:
        raise WorkflowLoadError("workflow at workflow_url must not be empty")

    return parsed_json


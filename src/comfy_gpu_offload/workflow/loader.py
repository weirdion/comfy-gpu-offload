"""Helpers for loading ComfyUI workflow JSON and guarding payload sizes."""

import json
from pathlib import Path
from typing import Any, Mapping

DEFAULT_MAX_PAYLOAD_BYTES = 9_500_000  # conservative vs RunPod 10 MB limit


class WorkflowLoadError(ValueError):
    """Raised when a workflow cannot be loaded or is invalid."""


def load_workflow_from_path(path: Path, *, max_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES) -> dict[str, Any]:
    """Load and validate a workflow JSON file from disk with size guard."""
    if not path.exists():
        raise WorkflowLoadError(f"Workflow file not found: {path}")
    size = path.stat().st_size
    if size <= 0:
        raise WorkflowLoadError(f"Workflow file is empty: {path}")
    if size > max_bytes:
        raise WorkflowLoadError(f"Workflow file too large ({size} bytes), limit {max_bytes} bytes")

    try:
        data = path.read_text(encoding="utf-8")
        parsed = json.loads(data)
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowLoadError(f"Failed to read/parse workflow JSON: {exc}") from exc

    if not isinstance(parsed, Mapping):
        raise WorkflowLoadError("Workflow JSON must be an object")
    if not parsed:
        raise WorkflowLoadError("Workflow JSON must not be empty")
    return dict(parsed)


def ensure_payload_size(payload: Mapping[str, Any], *, max_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES) -> None:
    """Validate that a payload fits within the size budget when JSON-encoded."""
    try:
        encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise WorkflowLoadError(f"Failed to encode payload to JSON: {exc}") from exc
    if len(encoded) > max_bytes:
        raise WorkflowLoadError(
            f"Payload too large ({len(encoded)} bytes), limit {max_bytes} bytes; "
            "reduce workflow size or strip unused assets."
        )

"""Lightweight workflow schema validation."""

from typing import Any, Mapping


def validate_workflow_schema(workflow: Mapping[str, Any]) -> None:
    """Ensure the workflow resembles a ComfyUI API-format workflow."""
    if "nodes" not in workflow:
        raise ValueError("workflow JSON must include a 'nodes' key")
    if not isinstance(workflow["nodes"], list):
        raise ValueError("'nodes' must be a list")
    # Optional: future fields checks (e.g., 'links') could be added here.

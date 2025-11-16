"""ComfyUI node for offloading workflows to RunPod."""

import json
from collections.abc import Callable
from typing import Any, cast

from comfy_gpu_offload.api import RunpodClient
from comfy_gpu_offload.config import ConfigError, RunpodConfig, load_runpod_config
from comfy_gpu_offload.workflow import (
    BuildPayloadError,
    ImagePayload,
    RunpodInputPayload,
    WorkflowLoadError,
    build_run_payload,
    ensure_payload_size,
    load_workflow_from_path,
)


def _default_client_factory(config: RunpodConfig) -> RunpodClient:
    return RunpodClient(config)


class RunPodRemoteExecute:
    """Submit a ComfyUI workflow to RunPod serverless and return results."""

    CATEGORY = "RunPod"
    FUNCTION = "execute"
    RETURN_TYPES = ("STRING", "STRING", "STRING")  # status, job_id, output_json
    RETURN_NAMES = ("status", "job_id", "output_json")
    OUTPUT_NODE = True

    client_factory: Callable[[RunpodConfig], RunpodClient] = _default_client_factory
    max_payload_bytes: int | None = None  # override for tests; defaults to loader default

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:  # noqa: N802 (ComfyUI requires this name)
        return {
            "required": {
                "workflow_json": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "forceInput": True,
                        "placeholder": "Paste ComfyUI API-format workflow JSON",
                    },
                ),
                "use_runpod": ("BOOLEAN", {"default": True}),
                "workflow_path": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "placeholder": "/path/to/workflow_api.json (optional, overrides workflow_json)",
                    },
                ),
            },
            "optional": {
                "params_json": (
                    "STRING",
                    {"multiline": True, "default": "{}", "placeholder": '{"seed": 1234}'},
                ),
                "images_json": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "[]",
                        "placeholder": '[{"name": "init.png", "image": "...base64..."}]',
                    },
                ),
                "timeout_seconds": ("FLOAT", {"default": 900.0, "min": 1.0, "max": 3600.0}),
            },
        }

    def execute(
        self,
        workflow_json: str,
        use_runpod: bool = True,
        params_json: str = "{}",
        images_json: str = "[]",
        timeout_seconds: float | None = None,
        workflow_path: str = "",
    ) -> tuple[str, str, str]:
        if not use_runpod:
            return ("disabled", "", "{}")

        if workflow_path.strip():
            workflow = self._load_workflow_from_path(workflow_path.strip())
        else:
            workflow = self._parse_json_mapping(workflow_json, "workflow_json")

        params = self._parse_json_mapping(params_json, "params_json", allow_empty=True)
        images = self._parse_json_sequence(images_json, "images_json")

        try:
            config = load_runpod_config()
        except ConfigError as exc:
            raise RuntimeError(f"RunPod configuration error: {exc}") from exc

        payload: RunpodInputPayload
        try:
            payload = build_run_payload(
                workflow=workflow,
                images=cast(list[ImagePayload], images),
                params=params,
            )
            if self.max_payload_bytes is not None:
                ensure_payload_size(payload, max_bytes=self.max_payload_bytes)
        except BuildPayloadError as exc:
            raise RuntimeError(f"Invalid payload: {exc}") from exc
        except WorkflowLoadError as exc:
            raise RuntimeError(f"Payload too large: {exc}") from exc

        client = self.client_factory(config)

        job_id = client.submit_job(payload)
        status = client.poll_job(job_id, timeout_seconds=timeout_seconds)

        output_json = json.dumps(status.output or {})
        return (status.status, job_id, output_json)

    def _load_workflow_from_path(self, path_str: str) -> dict[str, Any]:
        try:
            path = Path(path_str)
        except OSError as exc:
            raise RuntimeError(f"Invalid workflow_path: {exc}") from exc

        try:
            workflow = load_workflow_from_path(path)
        except Exception as exc:
            raise RuntimeError(f"Failed to load workflow from path: {exc}") from exc

        # Guard payload size if configured
        max_bytes = self.max_payload_bytes
        if max_bytes is not None:
            ensure_payload_size({"workflow": workflow}, max_bytes=max_bytes)
        return workflow

    @staticmethod
    def _parse_json_mapping(value: str, field: str, *, allow_empty: bool = False) -> dict[str, Any]:
        try:
            parsed = json.loads(value) if value else {}
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{field} is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError(f"{field} must be a JSON object")
        if not parsed and not allow_empty:
            raise RuntimeError(f"{field} must not be empty")
        return parsed

    @staticmethod
    def _parse_json_sequence(value: str, field: str) -> list[dict[str, Any]]:
        if not value:
            return []
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{field} is not valid JSON: {exc}") from exc
        if not isinstance(parsed, list):
            raise RuntimeError(f"{field} must be a JSON array")
        for item in parsed:
            if not isinstance(item, dict):
                raise RuntimeError(f"each item in {field} must be an object")
        return parsed

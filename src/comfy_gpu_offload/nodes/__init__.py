"""ComfyUI node definitions for RunPod offload."""

from .runpod_remote_execute import RunPodRemoteExecute

NODE_CLASS_MAPPINGS: dict[str, type] = {
    "RunPodRemoteExecute": RunPodRemoteExecute,
}

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "RunPodRemoteExecute": "RunPod Remote Execute",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "RunPodRemoteExecute"]

"""Helpers for constructing RunPod payloads from ComfyUI workflows."""

from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any, NotRequired, TypedDict


class BuildPayloadError(ValueError):
    """Raised when payload construction fails due to invalid inputs."""


class ImagePayload(TypedDict):
    name: str
    image: str  # base64 string without data URI prefix
    type: NotRequired[str]


class RunpodInputPayload(TypedDict, total=False):
    workflow: MutableMapping[str, Any]
    images: list[ImagePayload]
    params: MutableMapping[str, Any]


def build_run_payload(
    *,
    workflow: Mapping[str, Any],
    images: Sequence[ImagePayload] | None = None,
    params: Mapping[str, Any] | None = None,
) -> RunpodInputPayload:
    """Validate and build the payload for RunPod /run."""
    if not isinstance(workflow, Mapping):
        raise BuildPayloadError("workflow must be a mapping")
    if not workflow:
        raise BuildPayloadError("workflow must not be empty")

    payload: RunpodInputPayload = {"workflow": dict(workflow)}

    if images:
        validated_images: list[ImagePayload] = []
        for image in images:
            name = image.get("name")
            data = image.get("image")
            if not isinstance(name, str) or not name:
                raise BuildPayloadError("each image must include a non-empty 'name'")
            if not isinstance(data, str) or not data:
                raise BuildPayloadError("each image must include a non-empty 'image' base64 string")
            img_entry: ImagePayload = {"name": name, "image": data}
            maybe_type = image.get("type")
            if maybe_type:
                if not isinstance(maybe_type, str):
                    raise BuildPayloadError("'type' must be a string if provided")
                img_entry["type"] = maybe_type
            validated_images.append(img_entry)
        payload["images"] = validated_images

    if params:
        if not isinstance(params, Mapping):
            raise BuildPayloadError("params must be a mapping if provided")
        payload["params"] = dict(params)

    return payload

from typing import Any

import pytest

from comfy_gpu_offload.workflow import BuildPayloadError, build_run_payload


def test_build_run_payload_happy_path() -> None:
    payload = build_run_payload(
        workflow={"nodes": []},
        images=[{"name": "input.png", "image": "ZmFrZQ==", "type": "base64"}],
        params={"seed": 123},
    )

    assert payload["workflow"] == {"nodes": []}
    assert payload["images"][0]["name"] == "input.png"
    assert payload["images"][0]["image"] == "ZmFrZQ=="
    assert payload["images"][0]["type"] == "base64"
    assert payload["params"] == {"seed": 123}


@pytest.mark.parametrize(
    "workflow",
    [
        {},
        [],
        "not-a-mapping",
    ],
)
def test_build_run_payload_invalid_workflow(workflow: Any) -> None:
    with pytest.raises(BuildPayloadError):
        build_run_payload(workflow=workflow)  # type: ignore[arg-type]


def test_build_run_payload_rejects_bad_images() -> None:
    with pytest.raises(BuildPayloadError):
        build_run_payload(workflow={"nodes": []}, images=[{"name": "", "image": "dGVzdA=="}])  # type: ignore[list-item]

    with pytest.raises(BuildPayloadError):
        build_run_payload(workflow={"nodes": []}, images=[{"name": "x", "image": ""}])  # type: ignore[list-item]

    with pytest.raises(BuildPayloadError):
        build_run_payload(workflow={"nodes": []}, images=[{"name": "x", "image": "ok", "type": 123}])  # type: ignore[list-item]


def test_build_run_payload_rejects_bad_params() -> None:
    with pytest.raises(BuildPayloadError):
        build_run_payload(workflow={"nodes": []}, params="nope")  # type: ignore[arg-type]


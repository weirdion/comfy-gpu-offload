from typing import Any, cast

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
        build_run_payload(workflow=workflow)


def test_build_run_payload_rejects_bad_images() -> None:
    with pytest.raises(BuildPayloadError):
        build_run_payload(
            workflow={"nodes": []},
            images=[cast(Any, {"name": "", "image": "dGVzdA==", "type": "base64"})],
        )

    with pytest.raises(BuildPayloadError):
        build_run_payload(
            workflow={"nodes": []},
            images=[cast(Any, {"name": "x", "image": "", "type": "base64"})],
        )

    with pytest.raises(BuildPayloadError):
        build_run_payload(
            workflow={"nodes": []},
            images=[cast(Any, {"name": "x", "image": "ok", "type": 123})],
        )


def test_build_run_payload_rejects_bad_params() -> None:
    with pytest.raises(BuildPayloadError):
        build_run_payload(workflow={"nodes": []}, params=cast(Any, "nope"))

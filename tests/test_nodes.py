import json
from typing import Any

import pytest

from comfy_gpu_offload.api import RunpodStatus
from comfy_gpu_offload.config import RunpodConfig
from comfy_gpu_offload.nodes.runpod_remote_execute import RunPodRemoteExecute


class FakeClient:
    def __init__(self) -> None:
        self.submitted_payload: Any | None = None
        self.job_id = "job-xyz"
        self.status = RunpodStatus.COMPLETED
        self.output = {"ok": True}

    def submit_job(self, payload: Any) -> str:
        self.submitted_payload = payload
        return self.job_id

    def poll_job(self, job_id: str, timeout_seconds: float | None = None):
        class Status:
            def __init__(self, outer: FakeClient) -> None:
                self.status = outer.status
                self.output = outer.output
        return Status(self)


def test_node_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = FakeClient()
    node = RunPodRemoteExecute()

    node.client_factory = lambda _config: fake_client  # type: ignore[assignment]
    monkeypatch.setenv("RUNPOD_API_KEY", "k")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "e")

    status, job_id, output_json = node.execute(
        workflow_json='{"nodes": []}',
        use_runpod=True,
        params_json='{"seed":123}',
        images_json='[{"name":"x","image":"ZmFrZQ=="}]',
        timeout_seconds=1.0,
    )

    assert status == RunpodStatus.COMPLETED
    assert job_id == fake_client.job_id
    assert json.loads(output_json) == fake_client.output
    assert fake_client.submitted_payload["workflow"] == {"nodes": []}


def test_node_skips_when_disabled() -> None:
    node = RunPodRemoteExecute()
    status, job_id, output_json = node.execute(workflow_json="{}", use_runpod=False)
    assert status == "disabled"
    assert job_id == ""
    assert output_json == "{}"


def test_node_validates_workflow_json() -> None:
    node = RunPodRemoteExecute()
    with pytest.raises(RuntimeError):
        node.execute(workflow_json="not-json", use_runpod=True)


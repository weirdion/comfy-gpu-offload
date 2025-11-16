import json
from pathlib import Path
from typing import Any, Callable, cast

import pytest

from comfy_gpu_offload.api import RunpodStatus, RunpodClient
from comfy_gpu_offload.nodes.runpod_remote_execute import RunPodRemoteExecute


class FakeClient(RunpodClient):  # type: ignore[misc]
    def __init__(self) -> None:
        self.submitted_payload: dict[str, Any] | None = None
        self.job_id = "job-abc"
        self.output = {"ok": True}

    def submit_job(self, payload: Any) -> str:  # type: ignore[override]
        self.submitted_payload = payload
        return self.job_id

    def poll_job(self, job_id: str, timeout_seconds: float | None = None):  # type: ignore[override]
        class Status:
            def __init__(self, outer: FakeClient) -> None:
                self.status = RunpodStatus.COMPLETED
                self.output = outer.output

        return Status(self)


def test_node_loads_workflow_from_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    node = RunPodRemoteExecute()
    fake_client = FakeClient()

    def factory(_config: Any) -> RunpodClient:
        return cast(RunpodClient, fake_client)

    node.client_factory = factory
    node.max_payload_bytes = 1_000_000

    wf_path = tmp_path / "workflow_api.json"
    wf_path.write_text(json.dumps({"nodes": []}), encoding="utf-8")

    monkeypatch.setenv("RUNPOD_API_KEY", "k")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "e")

    status, job_id, output_json = node.execute(
        workflow_json="{}",  # ignored when workflow_path provided
        workflow_path=str(wf_path),
    )

    assert status == RunpodStatus.COMPLETED
    assert job_id == fake_client.job_id
    assert fake_client.submitted_payload is not None
    assert fake_client.submitted_payload["workflow"] == {"nodes": []}
    assert json.loads(output_json) == fake_client.output


def test_node_rejects_missing_workflow_path() -> None:
    node = RunPodRemoteExecute()
    with pytest.raises(RuntimeError):
        node._load_workflow_from_path("/this/path/does/not/exist")


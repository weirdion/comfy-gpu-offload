import json
from typing import Any

import pytest

from comfy_gpu_offload.workflow import WorkflowLoadError, fetch_workflow_from_url


class FakeResp:
    def __init__(self, status_code: int, content: bytes) -> None:
        self.status_code = status_code
        self.content = content


def test_fetch_workflow_from_url_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, timeout: float, verify: bool) -> FakeResp:
        assert url == "https://example.com/workflow"
        assert verify is True
        return FakeResp(200, json.dumps({"nodes": []}).encode("utf-8"))

    monkeypatch.setattr("requests.get", fake_get)
    wf = fetch_workflow_from_url("https://example.com/workflow")
    assert wf == {"nodes": []}


def test_fetch_workflow_from_url_http_requires_disable_verify(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(WorkflowLoadError):
        fetch_workflow_from_url("http://insecure.local")


def test_fetch_workflow_from_url_too_large(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, timeout: float, verify: bool) -> FakeResp:
        return FakeResp(200, b"x" * 2_000_000)

    monkeypatch.setattr("requests.get", fake_get)
    with pytest.raises(WorkflowLoadError):
        fetch_workflow_from_url("https://example.com/workflow", max_bytes=1_000_000)


def test_fetch_workflow_from_url_bad_status(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, timeout: float, verify: bool) -> FakeResp:
        return FakeResp(500, b"error")

    monkeypatch.setattr("requests.get", fake_get)
    with pytest.raises(WorkflowLoadError):
        fetch_workflow_from_url("https://example.com/workflow")


from typing import Any, cast

import pytest
import requests

from comfy_gpu_offload.api import (
    RunpodApiError,
    RunpodCancelledError,
    RunpodClient,
    RunpodJobError,
    RunpodStatus,
    RunpodTimeoutError,
)
from comfy_gpu_offload.config import RunpodConfig


class FakeResponse:
    def __init__(self, status_code: int, json_data: Any) -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = "" if json_data is None else str(json_data)

    def json(self) -> Any:
        return self._json_data


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        timeout: float,
        verify: bool,
        **kwargs: Any,
    ) -> FakeResponse:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "timeout": timeout,
                "verify": verify,
                "kwargs": kwargs,
            }
        )
        if not self.responses:
            raise AssertionError("No more fake responses available")
        return self.responses.pop(0)


def make_client(responses: list[FakeResponse]) -> tuple[RunpodClient, FakeSession]:
    session = FakeSession(responses)
    cfg = RunpodConfig(api_key="k", endpoint_id="e")
    return RunpodClient(cfg, session=cast(requests.Session, session)), session


def test_submit_job_returns_id_and_sets_auth_header() -> None:
    client, session = make_client(
        [FakeResponse(200, {"id": "job-123", "status": RunpodStatus.IN_QUEUE})]
    )

    job_id = client.submit_job({"workflow": {"foo": "bar"}})

    assert job_id == "job-123"
    assert session.calls[0]["headers"]["Authorization"].startswith("Bearer ")
    assert session.calls[0]["verify"] is True


def test_get_job_status_parses_output() -> None:
    client, _ = make_client(
        [
            FakeResponse(
                200,
                {"id": "job-123", "status": RunpodStatus.COMPLETED, "output": {"ok": True}},
            )
        ]
    )

    status = client.get_job_status("job-123")

    assert status.job_id == "job-123"
    assert status.status == RunpodStatus.COMPLETED
    assert status.output == {"ok": True}


def test_poll_job_completes() -> None:
    client, _ = make_client(
        [
            FakeResponse(200, {"id": "job-123", "status": RunpodStatus.IN_PROGRESS}),
            FakeResponse(
                200,
                {"id": "job-123", "status": RunpodStatus.COMPLETED, "output": {"result": "ok"}},
            ),
        ]
    )

    status = client.poll_job("job-123", poll_interval_seconds=0.0, timeout_seconds=1.0)

    assert status.status == RunpodStatus.COMPLETED
    assert status.output == {"result": "ok"}


def test_poll_job_raises_on_failure_status() -> None:
    client, _ = make_client(
        [FakeResponse(200, {"id": "job-123", "status": RunpodStatus.FAILED, "error": "boom"})]
    )

    with pytest.raises(RunpodJobError):
        client.poll_job("job-123", poll_interval_seconds=0.0, timeout_seconds=1.0)


def test_poll_job_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = make_client(
        [
            FakeResponse(200, {"id": "job-123", "status": RunpodStatus.IN_PROGRESS}),
            FakeResponse(200, {"id": "job-123", "status": RunpodStatus.IN_PROGRESS}),
        ]
    )

    times = iter([0.0, 0.4, 1.0])

    def fake_monotonic() -> float:
        return next(times)

    monkeypatch.setattr("time.monotonic", fake_monotonic)
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    with pytest.raises(RunpodTimeoutError):
        client.poll_job("job-123", poll_interval_seconds=0.0, timeout_seconds=0.5)


def test_poll_job_reports_progress_and_can_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = make_client(
        [
            FakeResponse(200, {"id": "job-123", "status": RunpodStatus.IN_PROGRESS}),
        ]
    )
    seen_statuses: list[str] = []

    def on_progress(status: Any) -> None:
        seen_statuses.append(status.status)

    def should_continue() -> bool:
        return False

    times = iter([0.0, 0.1])
    monkeypatch.setattr("time.monotonic", lambda: next(times))
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    with pytest.raises(RunpodCancelledError):
        client.poll_job(
            "job-123",
            poll_interval_seconds=0.0,
            timeout_seconds=1.0,
            on_progress=on_progress,
            should_continue=should_continue,
        )

    assert seen_statuses == [RunpodStatus.IN_PROGRESS]


def test_http_error_raises_api_error() -> None:
    client, _ = make_client([FakeResponse(500, {"error": "server"})])

    with pytest.raises(RunpodApiError):
        client.submit_job({"input": {}})


def test_invalid_json_raises_api_error() -> None:
    class BadResponse(FakeResponse):
        def json(self) -> Any:
            raise ValueError("not json")

    client, _ = make_client([BadResponse(200, None)])

    with pytest.raises(RunpodApiError):
        client.submit_job({})

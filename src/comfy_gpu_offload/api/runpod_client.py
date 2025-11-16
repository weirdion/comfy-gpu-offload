"""Typed RunPod API client with minimal retry/backoff and polling."""

import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import requests
from requests import Response
from requests.exceptions import RequestException

from comfy_gpu_offload.config import RunpodConfig


class RunpodApiError(RuntimeError):
    """Raised when the RunPod API returns an error or an unexpected response."""


class RunpodCancelledError(RunpodApiError):
    """Raised when polling is cancelled by the caller."""


class RunpodTimeoutError(RunpodApiError):
    """Raised when polling exceeds the configured timeout."""


class RunpodJobError(RunpodApiError):
    """Raised when a job finishes unsuccessfully (status FAILED or CANCELLED)."""


class RunpodStatus:
    IN_PROGRESS = "IN_PROGRESS"
    IN_QUEUE = "IN_QUEUE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    TERMINAL = {COMPLETED, FAILED, CANCELLED}


@dataclass(frozen=True, slots=True)
class JobStatus:
    job_id: str
    status: str
    output: Any | None = None
    error: str | None = None

    @property
    def is_terminal(self) -> bool:
        return self.status in RunpodStatus.TERMINAL


class RunpodClient:
    def __init__(self, config: RunpodConfig, session: requests.Session | None = None) -> None:
        self._config = config
        self._session = session or requests.Session()
        base = config.base_url.rstrip("/")
        self._endpoint_base = f"{base}/v2/{config.endpoint_id}"

    def submit_job(self, input_payload: Mapping[str, Any]) -> str:
        """Submit an async job; returns job ID."""
        body = {"input": dict(input_payload)}
        data = self._request_json("POST", "/run", json=body)
        job_id = data.get("id")
        if not isinstance(job_id, str) or not job_id:
            raise RunpodApiError("RunPod response missing job id")
        return job_id

    def get_job_status(self, job_id: str) -> JobStatus:
        """Fetch job status once."""
        data = self._request_json("GET", f"/status/{job_id}")
        status = data.get("status")
        if not isinstance(status, str):
            raise RunpodApiError("RunPod status response missing status field")
        output = data.get("output")
        error = data.get("error")
        return JobStatus(job_id=str(data.get("id", job_id)), status=status, output=output, error=error)

    def cancel_job(self, job_id: str) -> JobStatus:
        data = self._request_json("POST", f"/cancel/{job_id}")
        status = data.get("status")
        return JobStatus(job_id=job_id, status=status or RunpodStatus.CANCELLED, output=data.get("output"))

    def poll_job(
        self,
        job_id: str,
        *,
        poll_interval_seconds: float | None = None,
        timeout_seconds: float | None = None,
        on_progress: Callable[[JobStatus], None] | None = None,
        should_continue: Callable[[], bool] | None = None,
    ) -> JobStatus:
        """Poll until a job reaches a terminal status or times out."""
        poll_interval = poll_interval_seconds or self._config.poll_interval_seconds
        timeout = timeout_seconds or self._config.max_poll_duration_seconds
        deadline = time.monotonic() + timeout

        while True:
            status = self.get_job_status(job_id)
            if on_progress:
                on_progress(status)

            if status.is_terminal:
                if status.status == RunpodStatus.COMPLETED:
                    return status
                raise RunpodJobError(f"Job {job_id} finished with status {status.status}: {status.error}")

            now = time.monotonic()
            if now >= deadline:
                raise RunpodTimeoutError(f"Polling timeout exceeded for job {job_id}")

            if should_continue is not None and not should_continue():
                raise RunpodCancelledError(f"Polling cancelled by caller for job {job_id}")

            remaining = deadline - now
            sleep_for = min(poll_interval, max(0.0, remaining))
            time.sleep(sleep_for)

    def _request_json(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = self._endpoint_base + path
        headers = kwargs.pop("headers", {})
        # Avoid logging secrets; do not expose api_key.
        headers.setdefault("Authorization", f"Bearer {self._config.api_key}")
        headers.setdefault("Content-Type", "application/json")

        try:
            response = self._session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self._config.request_timeout_seconds,
                verify=self._config.verify_tls,
                **kwargs,
            )
        except RequestException as exc:
            raise RunpodApiError(f"RunPod request failed: {exc!s}") from exc

        self._raise_for_status(response, method, url)
        return self._parse_json(response, url)

    @staticmethod
    def _raise_for_status(response: Response, method: str, url: str) -> None:
        if response.status_code >= 400:
            snippet = response.text[:500] if response.text else ""
            raise RunpodApiError(
                f"RunPod API returned {response.status_code} for {method} {url}: {snippet}"
            )

    @staticmethod
    def _parse_json(response: Response, url: str) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError as exc:
            raise RunpodApiError(f"Invalid JSON in response from {url}") from exc
        if not isinstance(data, dict):
            raise RunpodApiError(f"Unexpected JSON type from {url}: expected object")
        return data

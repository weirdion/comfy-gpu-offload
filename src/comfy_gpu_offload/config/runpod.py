"""RunPod configuration models and loaders."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


class ConfigError(ValueError):
    """Raised when configuration is missing or invalid."""


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ConfigError(f"Invalid boolean value: {value!r}")


def _parse_float(value: str | None, *, default: float, name: str) -> float:
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError as err:
        raise ConfigError(f"Invalid float for {name}: {value!r}") from err
    if parsed <= 0:
        raise ConfigError(f"{name} must be greater than 0")
    return parsed


def _require(value: str | None, *, name: str) -> str:
    if value is None or value.strip() == "":
        raise ConfigError(f"Missing required configuration: {name}")
    return value


@dataclass(frozen=True, slots=True)
class RunpodConfig:
    api_key: str
    endpoint_id: str
    base_url: str = "https://api.runpod.io"
    request_timeout_seconds: float = 30.0
    verify_tls: bool = True
    poll_interval_seconds: float = 3.0
    max_poll_duration_seconds: float = 900.0  # 15 minutes

    @staticmethod
    def env_keys() -> dict[str, str]:
        return {
            "api_key": "RUNPOD_API_KEY",
            "endpoint_id": "RUNPOD_ENDPOINT_ID",
            "base_url": "RUNPOD_BASE_URL",
            "request_timeout_seconds": "RUNPOD_REQUEST_TIMEOUT",
            "verify_tls": "RUNPOD_VERIFY_TLS",
            "poll_interval_seconds": "RUNPOD_POLL_INTERVAL",
            "max_poll_duration_seconds": "RUNPOD_MAX_POLL_DURATION",
        }


def load_runpod_config(env: Mapping[str, str] | None = None) -> RunpodConfig:
    """Load RunPod configuration from environment variables with validation."""
    source_env: Mapping[str, str] = env or os.environ
    keys = RunpodConfig.env_keys()

    api_key = _require(source_env.get(keys["api_key"]), name=keys["api_key"])
    endpoint_id = _require(
        source_env.get(keys["endpoint_id"]),
        name=keys["endpoint_id"],
    )

    base_url = source_env.get(keys["base_url"], RunpodConfig.base_url)
    request_timeout_seconds = _parse_float(
        source_env.get(keys["request_timeout_seconds"]),
        default=RunpodConfig.request_timeout_seconds,
        name=keys["request_timeout_seconds"],
    )
    verify_tls = _parse_bool(
        source_env.get(keys["verify_tls"]),
        default=RunpodConfig.verify_tls,
    )
    poll_interval_seconds = _parse_float(
        source_env.get(keys["poll_interval_seconds"]),
        default=RunpodConfig.poll_interval_seconds,
        name=keys["poll_interval_seconds"],
    )
    max_poll_duration_seconds = _parse_float(
        source_env.get(keys["max_poll_duration_seconds"]),
        default=RunpodConfig.max_poll_duration_seconds,
        name=keys["max_poll_duration_seconds"],
    )

    return RunpodConfig(
        api_key=api_key,
        endpoint_id=endpoint_id,
        base_url=base_url,
        request_timeout_seconds=request_timeout_seconds,
        verify_tls=verify_tls,
        poll_interval_seconds=poll_interval_seconds,
        max_poll_duration_seconds=max_poll_duration_seconds,
    )


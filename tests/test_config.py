import pytest

from comfy_gpu_offload.config import ConfigError, RunpodConfig, load_runpod_config


def test_load_runpod_config_happy_path() -> None:
    env = {
        "RUNPOD_API_KEY": "dummy-key",
        "RUNPOD_ENDPOINT_ID": "endpoint-123",
    }
    cfg = load_runpod_config(env)

    assert cfg.api_key == "dummy-key"
    assert cfg.endpoint_id == "endpoint-123"
    assert cfg.base_url == "https://api.runpod.ai"
    assert cfg.request_timeout_seconds == 30.0
    assert cfg.verify_tls is True
    assert cfg.poll_interval_seconds == 3.0
    assert cfg.max_poll_duration_seconds == 900.0


def test_load_runpod_config_overrides_and_parsing() -> None:
    env = {
        "RUNPOD_API_KEY": "k",
        "RUNPOD_ENDPOINT_ID": "e",
        "RUNPOD_BASE_URL": "https://example.invalid",
        "RUNPOD_REQUEST_TIMEOUT": "10.5",
        "RUNPOD_VERIFY_TLS": "false",
        "RUNPOD_POLL_INTERVAL": "1.2",
        "RUNPOD_MAX_POLL_DURATION": "123",
    }
    cfg = load_runpod_config(env)

    assert cfg.base_url == "https://example.invalid"
    assert cfg.request_timeout_seconds == pytest.approx(10.5)
    assert cfg.verify_tls is False
    assert cfg.poll_interval_seconds == pytest.approx(1.2)
    assert cfg.max_poll_duration_seconds == pytest.approx(123.0)


@pytest.mark.parametrize(
    ("env", "expected_message"),
    [
        ({}, "RUNPOD_API_KEY"),
        ({"RUNPOD_API_KEY": "k"}, "RUNPOD_ENDPOINT_ID"),
    ],
)
def test_load_runpod_config_missing_required(env: dict[str, str], expected_message: str) -> None:
    with pytest.raises(ConfigError) as err:
        load_runpod_config(env)
    assert expected_message in str(err.value)


@pytest.mark.parametrize(
    "bad_env",
    [
        {"RUNPOD_API_KEY": "k", "RUNPOD_ENDPOINT_ID": "e", "RUNPOD_VERIFY_TLS": "maybe"},
        {"RUNPOD_API_KEY": "k", "RUNPOD_ENDPOINT_ID": "e", "RUNPOD_REQUEST_TIMEOUT": "0"},
    ],
)
def test_load_runpod_config_invalid_values(bad_env: dict[str, str]) -> None:
    with pytest.raises(ConfigError):
        load_runpod_config(bad_env)


def test_load_runpod_config_requires_https() -> None:
    env = {
        "RUNPOD_API_KEY": "k",
        "RUNPOD_ENDPOINT_ID": "e",
        "RUNPOD_BASE_URL": "http://insecure.example",
    }
    with pytest.raises(ConfigError):
        load_runpod_config(env)

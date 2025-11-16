import pytest

from comfy_gpu_offload.config import ConfigError, load_runpod_config


def test_base_url_must_be_https() -> None:
    env = {
        "RUNPOD_API_KEY": "k",
        "RUNPOD_ENDPOINT_ID": "e",
        "RUNPOD_BASE_URL": "http://insecure.example",
    }
    with pytest.raises(ConfigError):
        load_runpod_config(env)

from pathlib import Path

import pytest
from PIL import Image

from comfy_gpu_offload.io import (
    base64_to_image,
    image_to_base64,
    new_temp_dir,
    remove_path_safely,
    write_bytes_secure,
)


def test_new_temp_dir_and_permissions() -> None:
    path = new_temp_dir()
    try:
        assert path.exists()
        assert path.is_dir()
        assert oct(path.stat().st_mode & 0o777) == oct(0o700)
    finally:
        remove_path_safely(path)


def test_write_bytes_secure_sets_permissions(tmp_path: Path) -> None:
    file_path = tmp_path / "out.bin"
    written = write_bytes_secure(file_path, b"hello", mode=0o600)
    assert written.read_bytes() == b"hello"
    assert oct(written.stat().st_mode & 0o777) == oct(0o600)


def test_remove_path_safely_no_raise_on_missing(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    remove_path_safely(missing)  # Should not raise.


def test_image_base64_round_trip() -> None:
    image = Image.new("RGB", (2, 2), color=(255, 0, 0))
    encoded = image_to_base64(image, format="PNG")
    decoded = base64_to_image(encoded)

    assert decoded.size == (2, 2)
    assert decoded.mode == "RGB"


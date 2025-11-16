"""Temporary directory and file helpers with cautious permissions."""

import os
import shutil
import tempfile
from pathlib import Path


def new_temp_dir(prefix: str = "comfy-gpu-offload-") -> Path:
    """Create a temporary directory with restrictive permissions (0o700)."""
    path = Path(tempfile.mkdtemp(prefix=prefix))
    path.chmod(0o700)
    return path


def ensure_directory(path: Path, mode: int = 0o700) -> None:
    """Ensure a directory exists with the given permissions."""
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(mode)


def write_bytes_secure(path: Path, data: bytes, *, mode: int = 0o600) -> Path:
    """Write bytes to a file with restricted permissions."""
    ensure_directory(path.parent, 0o700)
    with open(path, "wb") as file:
        file.write(data)
    os.chmod(path, mode)
    return path


def remove_path_safely(path: Path) -> None:
    """Best-effort removal of a file or directory tree without raising if missing."""
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            path.unlink(missing_ok=True)
    except OSError:
        # Intentionally swallow errors to avoid cascading failures during cleanup.
        return

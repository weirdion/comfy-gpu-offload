import json
from pathlib import Path

import pytest

from comfy_gpu_offload.workflow import WorkflowLoadError, ensure_payload_size, load_workflow_from_path


def test_load_workflow_from_path_success(tmp_path: Path) -> None:
    wf = {"nodes": []}
    p = tmp_path / "workflow.json"
    p.write_text(json.dumps(wf), encoding="utf-8")

    loaded = load_workflow_from_path(p)
    assert loaded == wf


def test_load_workflow_from_path_missing(tmp_path: Path) -> None:
    with pytest.raises(WorkflowLoadError):
        load_workflow_from_path(tmp_path / "missing.json")


def test_load_workflow_from_path_too_large(tmp_path: Path) -> None:
    p = tmp_path / "big.json"
    p.write_text("x" * 20_000_000, encoding="utf-8")
    with pytest.raises(WorkflowLoadError):
        load_workflow_from_path(p, max_bytes=1_000_000)


def test_load_workflow_from_path_not_mapping(tmp_path: Path) -> None:
    p = tmp_path / "workflow.json"
    p.write_text(json.dumps([]), encoding="utf-8")
    with pytest.raises(WorkflowLoadError):
        load_workflow_from_path(p)


def test_ensure_payload_size_checks_limit() -> None:
    small = {"a": "b"}
    ensure_payload_size(small, max_bytes=100)

    large = {"a": "x" * 200}
    with pytest.raises(WorkflowLoadError):
        ensure_payload_size(large, max_bytes=50)


import pytest

from comfy_gpu_offload.workflow import validate_workflow_schema


def test_validate_workflow_schema_happy_path() -> None:
    validate_workflow_schema({"nodes": []})


@pytest.mark.parametrize(
    "workflow",
    [
        {},
        {"nodes": "not-a-list"},
    ],
)
def test_validate_workflow_schema_rejects_invalid(workflow: dict) -> None:
    with pytest.raises(ValueError):
        validate_workflow_schema(workflow)


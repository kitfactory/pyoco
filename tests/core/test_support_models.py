from pyoco.core.models import TaskIO, TaskInfo, SupportFilters, SupportInfo
from pyoco.core.exceptions import MissingTaskMetadataError


def test_taskio_from_dict():
    data = {"name": "x", "type": "str", "required": True}
    taskio = TaskIO.from_dict(data)
    assert taskio.name == "x"
    assert taskio.type == "str"
    assert taskio.required is True


def test_support_models_roundtrip():
    io_in = TaskIO(name="a", type="int", required=True)
    io_out = TaskIO(name="b", type="str", required=False)
    info = TaskInfo(
        name="demo",
        summary="demo task",
        inputs=[io_in],
        outputs=[io_out],
        origin="pkg",
        tags=["tag1"],
    )
    filters = SupportFilters(name=["demo"], origin=["pkg"], tag=["tag1"])
    support = SupportInfo(kind="tasks", format="json", content="{}", filters=filters)
    assert info.name == "demo"
    assert support.filters.name == ["demo"]


def test_missing_task_metadata_error_fields():
    err = MissingTaskMetadataError("demo", ["summary", "inputs"])
    assert err.name == "demo"
    assert "summary" in err.fields

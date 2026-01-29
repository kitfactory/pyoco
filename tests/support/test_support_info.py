import json

from pyoco.core.models import TaskIO, TaskInfo
from pyoco.support.renderer import SupportInfoRenderer
from pyoco.support.service import SupportInfoService
from pyoco.support.writer import SupportInfoWriter


def _make_task(name, origin):
    return TaskInfo(
        name=name,
        summary=f"{name} summary",
        inputs=[TaskIO(name="x", type="str", required=True)],
        outputs=[TaskIO(name="y", type="str", required=False)],
        origin=origin,
        tags=["tag1"],
    )


def test_renderer_groups_and_sorts():
    tasks = [
        _make_task("b", "pkg"),
        _make_task("a", "pkg"),
        _make_task("c", "ext"),
    ]
    renderer = SupportInfoRenderer()
    payload = json.loads(renderer.render("tasks", tasks, "json"))
    origins = [group["origin"] for group in payload["groups"]]
    assert origins == ["ext", "pkg"]
    assert [t["name"] for t in payload["groups"][1]["tasks"]] == ["a", "b"]


def test_support_service_writes_output(tmp_path):
    class DummyCollector:
        def collect(self, config_path, filters):
            return [_make_task("a", "pkg")]

    class DummyRenderer:
        def render(self, kind, tasks, format):
            return "content"

    service = SupportInfoService(
        collector=DummyCollector(),
        renderer=DummyRenderer(),
        writer=SupportInfoWriter(),
    )
    out_path = tmp_path / "out.txt"
    service.build(kind="tasks", config_path="dummy.yaml", output_path=str(out_path))
    assert out_path.read_text() == "content"

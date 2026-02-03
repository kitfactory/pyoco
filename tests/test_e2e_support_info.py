import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from pyoco.support.service import SupportInfoService
from pyoco.core.exceptions import MissingTaskMetadataError


def _make_entry_point(name, hook):
    return SimpleNamespace(
        name=name,
        value=f"pkg:{hook.__name__}",
        module="pkg",
        load=lambda: hook,
    )


def _write_min_config(path):
    path.write_text(
        "version: 1\n"
        "tasks: {}\n"
    )


def test_e2e_support_info_tasks(tmp_path):
    config_path = tmp_path / "flow.yaml"
    _write_min_config(config_path)

    def plugin(registry):
        @registry.task(name="ext_task")
        def ext(ctx):
            return "ok"

        registry.task_info(
            name="ext_task",
            summary="demo task",
            inputs=[{"name": "x", "type": "str", "required": True}],
            outputs=[{"name": "y", "type": "str", "required": False}],
            origin="demo",
            tags=["tag1"],
        )

    with patch(
        "pyoco.discovery.loader.iter_entry_points",
        return_value=[_make_entry_point("demo", plugin)],
    ):
        content = SupportInfoService().build(
            kind="tasks",
            config_path=str(config_path),
            format="json",
        )
    data = json.loads(content)
    tasks = data["groups"][0]["tasks"]
    assert tasks[0]["name"] == "ext_task"


def test_e2e_support_info_missing_metadata(tmp_path):
    config_path = tmp_path / "flow.yaml"
    _write_min_config(config_path)

    def plugin(registry):
        @registry.task(name="ext_task")
        def ext(ctx):
            return "ok"

    with patch(
        "pyoco.discovery.loader.iter_entry_points",
        return_value=[_make_entry_point("demo", plugin)],
    ), pytest.raises(MissingTaskMetadataError):
        SupportInfoService().build(
            kind="tasks",
            config_path=str(config_path),
            format="json",
        )

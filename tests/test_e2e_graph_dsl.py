import json
from unittest.mock import patch

from pyoco.cli.main import main
from pyoco.core.engine import Engine
from pyoco.discovery.loader import TaskLoader
from pyoco.dsl.graph import build_flow_from_graph
from pyoco.schemas.config import PyocoConfig


def _write_e2e_files(tmp_path):
    module_path = tmp_path / "e2e_tasks.py"
    module_path.write_text(
        "from pyoco import task\n"
        "\n"
        "@task\n"
        "def prepare(ctx):\n"
        "    return 'prepared'\n"
        "\n"
        "@task\n"
        "def choose_mode(ctx):\n"
        "    return ctx.params.get('mode', 'batch')\n"
        "\n"
        "@task\n"
        "def run_batch(ctx):\n"
        "    count = ctx.params.get('batch_count', 0) + 1\n"
        "    ctx.params['batch_count'] = count\n"
        "    return count\n"
        "\n"
        "@task\n"
        "def process_item(ctx):\n"
        "    item = ctx.get_var('it')\n"
        "    idx = ctx.get_var('idx')\n"
        "    ctx.params.setdefault('processed', []).append(f'{idx}:{item}')\n"
        "    return item\n"
        "\n"
        "@task\n"
        "def poll_status(ctx):\n"
        "    polls = ctx.params.get('polls', 0) + 1\n"
        "    ctx.params['polls'] = polls\n"
        "    if polls >= 2:\n"
        "        ctx.params['done'] = True\n"
        "    return polls\n"
        "\n"
        "@task\n"
        "def finish(ctx):\n"
        "    return {\n"
        "        'batch_count': ctx.params.get('batch_count', 0),\n"
        "        'processed': ctx.params.get('processed', []),\n"
        "        'polls': ctx.params.get('polls', 0),\n"
        "        'done': ctx.params.get('done', False),\n"
        "    }\n",
        encoding="utf-8",
    )

    config_path = tmp_path / "flow.yaml"
    config_path.write_text(
        "version: 1\n"
        "pipes:\n"
        "  setup: \"prepare >> choose_mode\"\n"
        "tasks:\n"
        "  prepare:\n"
        "    callable: \"e2e_tasks:prepare\"\n"
        "  choose_mode:\n"
        "    callable: \"e2e_tasks:choose_mode\"\n"
        "  run_batch:\n"
        "    callable: \"e2e_tasks:run_batch\"\n"
        "  process_item:\n"
        "    callable: \"e2e_tasks:process_item\"\n"
        "  poll_status:\n"
        "    callable: \"e2e_tasks:poll_status\"\n"
        "  finish:\n"
        "    callable: \"e2e_tasks:finish\"\n"
        "    outputs:\n"
        "      - \"params.summary\"\n"
        "flow:\n"
        "  defaults:\n"
        "    mode: \"batch\"\n"
        "    items: [\"A\", \"B\", \"C\"]\n"
        "    done: false\n"
        "  graph: |\n"
        "    pipe(setup)\n"
        "    >> switch(on={{mode}}){\n"
        "      batch: repeat(count=2){ run_batch };\n"
        "      default: run_batch;\n"
        "    }\n"
        "    >> foreach(over={{items}}, item=it, index=idx){ process_item }\n"
        "    >> until(cond={{params.done}}, max_iter=5){ poll_status }\n"
        "    >> finish\n",
        encoding="utf-8",
    )
    return module_path, config_path


def test_e2e_graph_dsl_execution(tmp_path, monkeypatch):
    _, config_path = _write_e2e_files(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    config = PyocoConfig.from_yaml(str(config_path))
    loader = TaskLoader(config)
    loader.load()

    flow = build_flow_from_graph(
        graph=config.flow.graph,
        tasks=loader.tasks,
        pipes=config.pipes,
        flow_name="main",
    )
    ctx = Engine().run(flow, params=config.flow.defaults.copy())

    assert ctx.params["batch_count"] == 2
    assert ctx.params["processed"] == ["0:A", "1:B", "2:C"]
    assert ctx.params["polls"] == 2
    assert ctx.params["done"] is True
    assert ctx.params["summary"]["batch_count"] == 2
    assert ctx.params["summary"]["processed"] == ["0:A", "1:B", "2:C"]
    assert ctx.params["summary"]["polls"] == 2
    assert ctx.params["summary"]["done"] is True


def test_e2e_graph_dsl_check_dry_run(tmp_path, monkeypatch, capsys):
    _, config_path = _write_e2e_files(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    with patch(
        "sys.argv",
        ["pyoco", "check", "--config", str(config_path), "--dry-run", "--json"],
    ):
        main()

    out = capsys.readouterr().out
    json_payload = out[out.find("{") :]
    report = json.loads(json_payload)
    assert report["status"] == "ok"


def test_e2e_named_nodes_can_reuse_same_task_definition(tmp_path, monkeypatch):
    module_path = tmp_path / "named_tasks.py"
    module_path.write_text(
        "from pyoco import task\n"
        "\n"
        "@task\n"
        "def emit(ctx):\n"
        "    current = ctx.params.get('current', 0) + 1\n"
        "    ctx.params['current'] = current\n"
        "    return current\n"
        "\n"
        "@task\n"
        "def finish(ctx, first, second):\n"
        "    return {'first': first, 'second': second}\n",
        encoding="utf-8",
    )
    config_path = tmp_path / "named_flow.yaml"
    config_path.write_text(
        "version: 1\n"
        "tasks:\n"
        "  emit:\n"
        "    callable: \"named_tasks:emit\"\n"
        "  finish:\n"
        "    callable: \"named_tasks:finish\"\n"
        "    inputs:\n"
        "      first: \"$node.first.output\"\n"
        "      second: \"$node.second.output\"\n"
        "flow:\n"
        "  graph: |\n"
        "    first: emit >> second: emit >> finish\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    config = PyocoConfig.from_yaml(str(config_path))
    loader = TaskLoader(config)
    loader.load()

    flow = build_flow_from_graph(
        graph=config.flow.graph,
        tasks=loader.tasks,
        pipes=config.pipes,
        flow_name="main",
    )
    ctx = Engine().run(flow, params={})

    assert ctx.get_result("first") == 1
    assert ctx.get_result("second") == 2
    assert ctx.get_result("finish") == {"first": 1, "second": 2}

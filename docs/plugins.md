# Pyoco Plug-in Guide (v0.7.2)

Pyoco keeps its core small and lets domain packages extend it via Python entry points. Any package can advertise additional tasks under the `pyoco.tasks` group; pyoco discovers and registers them automatically at startup.

This model also lines up well with `pyoco-server`: once tasks are packaged as wheels, they are far easier to distribute to remote workers than loose local source files.

## Quickstart

1. **Declare the entry point** in your plug-in's `pyproject.toml`:

```toml
[project]
name = "pyoco-vision"
version = "0.1.0"

[project.entry-points."pyoco.tasks"]
vision = "pyoco_vision.entrypoint:register_tasks"
```

2. **Implement the hook**（Task サブクラスを推奨）:

```python
# pyoco_vision/entrypoint.py
from typing import Any
from pyoco.core.models import Task

class ImageClassifyTask(Task):
    def __init__(self):
        super().__init__(func=self.run, name="vision/image_classify")

    def run(self, ctx: Any, image_path: str):
        # ... do inference ...
        return {"label": "bunny", "confidence": 0.98}

def register_tasks(registry):
    registry.task_class(ImageClassifyTask)
    # registry.add(TaskWrapper(...)) なども利用可能
```

3. **Install the plug-in** into the same environment as pyoco. `TaskLoader` calls the hook during discovery. In `flow.yaml`, bind the public task name to a local name via `tasks.<local>.use`.

```yaml
tasks:
  classify:
    use: "vision/image_classify"

flow:
  graph: |
    classify
```

> 旧来の `@registry.task` デコレータも残っていますが、CLI で警告対象になります。新規開発は Task サブクラスで統一しましょう。

## Why this helps with `pyoco-server`

- `pyoco-server` is the distributed execution side: server + workers + remote run management.
- Packaged plug-ins are easier to move across workers because you can version and publish a wheel instead of copying project-local source by hand.
- If your workers are separated by role, packaged task sets also let operations decide which worker group should receive which plug-in.

Keep the detailed server setup in the `pyoco-server` docs. On the pyoco side, the important design point is simple: **package reusable tasks as plug-ins if you expect them to leave one machine.**

## Recommended project structure

```
pyoco-awesome/
├── pyproject.toml
├── README.md
├── src/pyoco_awesome/__init__.py
└── src/pyoco_awesome/entrypoint.py   # register_tasks lives here
```

- `pyproject.toml` の `project.entry-points."pyoco.tasks"` に hook を記述。
- エクスポートしたタスク名は `namespace/task_name` 形式を推奨します。`flow.yaml` では `tasks.<local>.use` でローカル名へ束ねます。
- `pyoco-server` で worker 配布を考える場合も、この package 形がそのまま流用しやすくなります。

## Local testing workflow

1. `uv pip install -e .` でプラグインを開発環境にインストール。
2. `pyoco plugins list --json` で検出を確認し、各タスクの `origin` が `task_class` になっているかチェック。
3. `pyoco plugins lint` を実行し、警告が出ないことを確認（callable 経由で登録するとここで警告されます）。
   - Each registered task must provide a usage description via `registry.task_info(..., usage=\"...\")`; otherwise lint fails.

プラグイン側の pytest 例:

```python
from types import SimpleNamespace
from pyoco.core.models import Task
from pyoco.discovery.plugins import PluginRegistry
from pyoco.discovery.loader import TaskLoader

class AwesomeTask(Task):
    def __init__(self):
        super().__init__(func=self.run, name="awesome")

    def run(self, ctx):
        return "awesome"

def test_register_tasks():
    dummy = SimpleNamespace(tasks={})
    loader = TaskLoader(dummy)
    registry = PluginRegistry(loader, "demo")
    registry.task_class(AwesomeTask)
    assert "awesome" in loader.tasks
```

## Task 実装のミニガイド

- 基本は **Task サブクラス**で実装し、`__init__` で `func=self.run` にしておくと CLI/Lint の表示が明確になります。
- 公開名は `namespace/task_name` を推奨します。`.` は Python module path と誤認しやすいため、区切りは `/` を優先します。
- 大きなデータは「ハンドル渡し」を優先：共有メモリ/メモリマップ/一時ファイルのパスなどを `ctx.artifacts` や `ctx.scratch` に置き、実体は必要なタスクでだけ読みます。
- 遅延パイプライン（例: DataPipe）は「実際に回すタスク」で1行ログを出すと理解が早まります。例: `[pipeline] B:resize -> C:augment -> G:train`
- outputs/input のメタは任意。必要なら `{"streaming": true, "handle": "memmap"}` のような辞書を `Task` に持たせ、PluginRegistry のメタとして渡すと CLI で可視化できます（書かなくても動作します）。
- 例外/警告には「直し方」をメッセージに含めると利用者が迷いません。

### サンプル: 遅延パイプライン

`docs/plugins_sample_datapipe.md` に、遅延パイプを定義する Task と、実行タスクでパイプ構成をログに出す最小プラグイン例を載せています。

## PluginRegistry API

`PluginRegistry` mirrors pyoco's internal task representation so plug-ins can stay lightweight:

| Method | Description |
| --- | --- |
| `registry.task_class(TaskSubclass, *args, name=None, **kwargs)` | Instantiate/register a Task サブクラス。 |
| `registry.task(name=None, inputs=None, outputs=None)` | **互換用**のデコレータ（内部で `CallablePluginTask` に変換）。 |
| `registry.register_callable(func, name=None, inputs=None, outputs=None)` | 同上（明示的に callable を登録する場合）。 |
| `registry.add(obj, name=None)` | Accepts an existing `Task` or `TaskWrapper`. Useful when plug-ins reuse flows/dsl fragments. |

All registered tasks appear inside `TaskLoader.tasks` and obey explicit-config overrides (inputs/outputs) when names match.
For lint compliance, pair each task with `registry.task_info(..., usage=\"...\")` so users can see how to use it. The recommended flow.yaml pattern is `tasks.<local_name>.use: "namespace/task_name"`.

## Inspecting plug-ins

The CLI surfaces packaged plug-ins:

```bash
pyoco plugins list
# or machine-readable
pyoco plugins list --json
```

Each entry reports the entry point name and module path. Use this to verify that your environment sees the plug-in before running flows.

## Testing suggestions

- Ship a small `tests/test_pyoco_plugin.py` alongside your plug-in that instantiates a `PluginRegistry` stub to validate registration.
- Add CI steps for `pyoco plugins lint --json` to ensure Task サブクラスで登録されているか。
- In pyoco itself we provide `tests/plugins/test_entrypoint_loader.py` to guarantee that the registry, loader, and CLI stay compatible.

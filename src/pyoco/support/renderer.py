import json
from typing import Dict, List, Tuple

from ..core.exceptions import InvalidFormatError
from ..core.models import TaskInfo


class SupportInfoRenderer:
    def render(self, kind: str, tasks: List[TaskInfo] | None, format: str) -> str:
        if format not in ("prompt", "json", "md"):
            raise InvalidFormatError(format)
        if kind == "guide":
            return self._render_guide(format)
        if kind not in ("tasks", "task"):
            raise ValueError(f"Unknown support kind: {kind}")
        return self._render_tasks(kind, tasks or [], format)

    def _render_tasks(self, kind: str, tasks: List[TaskInfo], format: str) -> str:
        groups = self._group_tasks(tasks)
        if format == "json":
            payload = {
                "kind": kind,
                "groups": [
                    {
                        "origin": origin,
                        "tasks": [self._task_to_dict(t) for t in items],
                    }
                    for origin, items in groups
                ],
            }
            return json.dumps(payload, indent=2)
        if format == "md":
            return self._render_tasks_md(kind, groups)
        return self._render_tasks_prompt(kind, groups)

    def _render_tasks_prompt(self, kind: str, groups: List[Tuple[str, List[TaskInfo]]]) -> str:
        lines = [f"Pyoco support ({kind})", ""]
        for origin, items in groups:
            lines.append(f"Origin: {origin}")
            for task in items:
                lines.append(f"- name: {task.name}")
                lines.append(f"  summary: {task.summary}")
                lines.append("  inputs:")
                for io in task.inputs:
                    lines.append(
                        f"    - {io.name} ({io.type}, required={io.required})"
                    )
                lines.append("  outputs:")
                for io in task.outputs:
                    lines.append(
                        f"    - {io.name} ({io.type}, required={io.required})"
                    )
                if task.tags:
                    lines.append(f"  tags: {', '.join(task.tags)}")
            lines.append("")
        return "\n".join(lines).rstrip()

    def _render_tasks_md(self, kind: str, groups: List[Tuple[str, List[TaskInfo]]]) -> str:
        lines = [f"# Pyoco support ({kind})", ""]
        for origin, items in groups:
            lines.append(f"## Origin: {origin}")
            for task in items:
                lines.append(f"### {task.name}")
                lines.append(task.summary)
                lines.append("")
                lines.append("**Inputs**")
                lines.append("")
                if task.inputs:
                    lines.append("| name | type | required | constraints |")
                    lines.append("|---|---|---|---|")
                    for io in task.inputs:
                        constraints = ", ".join(io.constraints) if io.constraints else ""
                        lines.append(
                            f"| {io.name} | {io.type} | {io.required} | {constraints} |"
                        )
                else:
                    lines.append("none")
                lines.append("")
                lines.append("**Outputs**")
                lines.append("")
                if task.outputs:
                    lines.append("| name | type | required | constraints |")
                    lines.append("|---|---|---|---|")
                    for io in task.outputs:
                        constraints = ", ".join(io.constraints) if io.constraints else ""
                        lines.append(
                            f"| {io.name} | {io.type} | {io.required} | {constraints} |"
                        )
                else:
                    lines.append("none")
                if task.tags:
                    lines.append("")
                    lines.append(f"**Tags**: {', '.join(task.tags)}")
                lines.append("")
        return "\n".join(lines).rstrip()

    def _task_to_dict(self, task: TaskInfo) -> Dict[str, object]:
        return {
            "name": task.name,
            "summary": task.summary,
            "inputs": [self._taskio_to_dict(io) for io in task.inputs],
            "outputs": [self._taskio_to_dict(io) for io in task.outputs],
            "origin": task.origin,
            "tags": task.tags or [],
        }

    def _taskio_to_dict(self, io) -> Dict[str, object]:
        return {
            "name": io.name,
            "type": io.type,
            "required": io.required,
            "constraints": io.constraints or [],
        }

    def _render_guide(self, format: str) -> str:
        guide = self._guide_payload()
        if format == "json":
            return json.dumps({"kind": "guide", **guide}, indent=2)
        if format == "md":
            return self._render_guide_md(guide)
        return self._render_guide_prompt(guide)

    def _guide_payload(self) -> Dict[str, str]:
        template = (
            "version: 1\n"
            "pipes:\n"
            "  setup: \"task_a >> task_b\"\n"
            "tasks:\n"
            "  local_task_a:\n"
            "    use: \"demo/task_a\"\n"
            "    inputs:\n"
            "      x: \"$ctx.params.mode\"\n"
            "  local_task_b:\n"
            "    use: \"demo/task_b\"\n"
            "    inputs:\n"
            "      input_a: \"$node.local_task_a.output\"\n"
            "flow:\n"
            "  graph: |\n"
            "    local_task_a\n"
            "    >> local_task_b\n"
            "    >> switch(on={{mode}}){\n"
            "      batch: repeat(count=2){ task_c };\n"
            "      default: task_c;\n"
            "    }\n"
            "    >> foreach(over={{items}}, item=it, index=idx){ task_d }\n"
            "    >> until(cond={{params.done}}, max_iter=5){ task_e }\n"
            "  defaults:\n"
            "    mode: \"batch\"\n"
            "    items: [\"x\", \"y\"]\n"
            "    done: false\n"
        )
        graph = (
            "- Use >> to define dependencies: A >> B means B depends on A.\n"
            "- Use pipe(NAME) to reuse pipelines defined under top-level pipes:.\n"
            "- Use switch(on=...){ ... } for branch selection.\n"
            "- Use repeat/foreach/until { ... } for loop controls.\n"
        )
        inputs = (
            "- Prefer $ctx.params.<key> to connect tasks via shared params.\n"
            "- If values would be overwritten or you need an explicit upstream output, use $node.<task_name>.output.\n"
            "- Use $env.<KEY> to reference allowed environment variables.\n"
            "- Prefer tasks.<local_name>.use for registered plug-in tasks. Public task names should use namespace/task_name,\n"
            "  for example demo/task_a. Keep tasks.<name>.callable for local overrides or migration.\n"
            "- Task discovery is not configured in flow.yaml. Use entry-point plugins (group 'pyoco.tasks')\n"
            "  or set PYOCO_DISCOVERY_MODULES to import extra modules. The 'discovery' config key is not supported.\n"
        )
        return {"template": template, "graph_syntax": graph, "input_refs": inputs}

    def _render_guide_prompt(self, guide: Dict[str, str]) -> str:
        return (
            "Pyoco flow.yaml guide\n\n"
            "Template:\n"
            f"{guide['template']}\n"
            "Graph syntax:\n"
            f"{guide['graph_syntax']}\n"
            "Input references:\n"
            f"{guide['input_refs']}"
        ).rstrip()

    def _render_guide_md(self, guide: Dict[str, str]) -> str:
        return (
            "# Pyoco flow.yaml guide\n\n"
            "## Template\n\n"
            "```yaml\n"
            f"{guide['template']}"
            "```\n\n"
            "## Graph syntax\n\n"
            f"{guide['graph_syntax']}\n"
            "## Input references\n\n"
            f"{guide['input_refs']}"
        ).rstrip()

    def _group_tasks(self, tasks: List[TaskInfo]) -> List[Tuple[str, List[TaskInfo]]]:
        groups: Dict[str, List[TaskInfo]] = {}
        for task in tasks:
            origin = task.origin or "unknown"
            groups.setdefault(origin, []).append(task)
        for items in groups.values():
            items.sort(key=lambda t: t.name)
        return [(origin, groups[origin]) for origin in sorted(groups.keys())]

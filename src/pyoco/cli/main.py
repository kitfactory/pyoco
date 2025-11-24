import argparse
import json
import sys
import os
import signal
import time
from types import SimpleNamespace
from ..schemas.config import PyocoConfig
from ..discovery.loader import TaskLoader
from ..core.models import Flow
from ..core.engine import Engine
from ..trace.console import ConsoleTraceBackend
from ..client import Client

def main():
    parser = argparse.ArgumentParser(description="Pyoco Workflow Engine")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a workflow")
    run_parser.add_argument("--config", required=True, help="Path to flow.yaml")
    run_parser.add_argument("--flow", default="main", help="Flow name to run")
    run_parser.add_argument("--trace", action="store_true", help="Enable tracing")
    run_parser.add_argument("--cute", action="store_true", default=True, help="Use cute trace style")
    run_parser.add_argument("--non-cute", action="store_false", dest="cute", help="Use plain trace style")
    # Allow overriding params via CLI
    run_parser.add_argument("--param", action="append", help="Override params (key=value)")
    run_parser.add_argument("--server", help="Server URL for remote execution")

    # Check command
    check_parser = subparsers.add_parser("check", help="Verify a workflow")
    check_parser.add_argument("--config", required=True, help="Path to flow.yaml")
    check_parser.add_argument("--flow", default="main", help="Flow name to check")
    check_parser.add_argument("--dry-run", action="store_true", help="Traverse flow without executing tasks")
    check_parser.add_argument("--json", action="store_true", help="Output report as JSON")

    # List tasks command
    list_parser = subparsers.add_parser("list-tasks", help="List available tasks")
    list_parser.add_argument("--config", required=True, help="Path to flow.yaml")

    # Server command
    server_parser = subparsers.add_parser("server", help="Manage Kanban Server")
    server_subparsers = server_parser.add_subparsers(dest="server_command")
    server_start = server_subparsers.add_parser("start", help="Start the server")
    server_start.add_argument("--host", default="0.0.0.0", help="Host to bind")
    server_start.add_argument("--port", type=int, default=8000, help="Port to bind")

    # Worker command
    worker_parser = subparsers.add_parser("worker", help="Manage Worker")
    worker_subparsers = worker_parser.add_subparsers(dest="worker_command")
    worker_start = worker_subparsers.add_parser("start", help="Start a worker")
    worker_start.add_argument("--server", required=True, help="Server URL")
    worker_start.add_argument("--config", required=True, help="Path to flow.yaml")
    worker_start.add_argument("--tags", help="Comma-separated tags")

    # Runs command
    runs_parser = subparsers.add_parser("runs", help="Manage runs")
    runs_subparsers = runs_parser.add_subparsers(dest="runs_command")
    
    runs_list = runs_subparsers.add_parser("list", help="List runs")
    runs_list.add_argument("--server", default="http://localhost:8000", help="Server URL")
    runs_list.add_argument("--status", help="Filter by status")
    runs_list.add_argument("--flow", help="Filter by flow name")
    runs_list.add_argument("--limit", type=int, help="Maximum number of runs to show")
    
    runs_show = runs_subparsers.add_parser("show", help="Show run details")
    runs_show.add_argument("run_id", help="Run ID")
    runs_show.add_argument("--server", default="http://localhost:8000", help="Server URL")
    
    runs_cancel = runs_subparsers.add_parser("cancel", help="Cancel a run")
    runs_cancel.add_argument("run_id", help="Run ID")
    runs_cancel.add_argument("--server", default="http://localhost:8000", help="Server URL")
    
    runs_inspect = runs_subparsers.add_parser("inspect", help="Inspect run details")
    runs_inspect.add_argument("run_id", help="Run ID")
    runs_inspect.add_argument("--server", default="http://localhost:8000", help="Server URL")
    runs_inspect.add_argument("--json", action="store_true", help="Output JSON payload")
    
    runs_logs = runs_subparsers.add_parser("logs", help="Show run logs")
    runs_logs.add_argument("run_id", help="Run ID")
    runs_logs.add_argument("--server", default="http://localhost:8000", help="Server URL")
    runs_logs.add_argument("--task", help="Filter logs by task")
    runs_logs.add_argument("--tail", type=int, help="Show last N log entries")
    runs_logs.add_argument("--follow", action="store_true", help="Stream logs until completion")
    runs_logs.add_argument("--allow-failure", action="store_true", help="Don't exit non-zero when run failed")

    plugins_parser = subparsers.add_parser("plugins", help="Inspect plug-in entry points")
    plugins_sub = plugins_parser.add_subparsers(dest="plugins_command")
    plugins_list = plugins_sub.add_parser("list", help="List discovered plug-ins")
    plugins_list.add_argument("--json", action="store_true", help="Output JSON payload")
    plugins_lint = plugins_sub.add_parser("lint", help="Validate plug-ins for upcoming requirements")
    plugins_lint.add_argument("--json", action="store_true", help="Output JSON payload")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load config only if needed
    config = None
    if hasattr(args, 'config') and args.config:
        try:
            config = PyocoConfig.from_yaml(args.config)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)

    # Discover tasks only if config is loaded
    loader = None
    if config:
        loader = TaskLoader(config)
        loader.load()

    if args.command == "list-tasks":
        if not loader:
             print("Error: Config not loaded.")
             sys.exit(1)
        print("Available tasks:")
        for name in loader.tasks:
            print(f" - {name}")
        return

    if args.command == "plugins":
        reports = _collect_plugin_reports()
        if args.plugins_command == "list":
            if getattr(args, "json", False):
                print(json.dumps(reports, indent=2))
            else:
                if not reports:
                    print("No plug-ins registered under group 'pyoco.tasks'.")
                else:
                    print("Discovered plug-ins:")
                    for info in reports:
                        mod = info.get("module") or info.get("value")
                        print(f" - {info.get('name')} ({mod})")
                        if info.get("error"):
                            print(f"     ⚠️  error: {info['error']}")
                            continue
                        for task in info.get("tasks", []):
                            warn_msg = "; ".join(task.get("warnings", [])) or "ok"
                            print(f"     • {task['name']} [{task['origin']}] ({warn_msg})")
                        for warn in info.get("warnings", []):
                            print(f"     ⚠️  {warn}")
        elif args.plugins_command == "lint":
            issues = []
            for info in reports:
                prefix = info["name"]
                if info.get("error"):
                    issues.append(f"{prefix}: {info['error']}")
                    continue
                for warn in info.get("warnings", []):
                    issues.append(f"{prefix}: {warn}")
                for task in info.get("tasks", []):
                    for warn in task.get("warnings", []):
                        issues.append(f"{prefix}.{task['name']}: {warn}")
            payload = {"issues": issues, "reports": reports}
            if getattr(args, "json", False):
                print(json.dumps(payload, indent=2))
            else:
                if not issues:
                    print("✅ All plug-ins look good.")
                else:
                    print("⚠️  Plug-in issues found:")
                    for issue in issues:
                        print(f" - {issue}")
            if issues:
                sys.exit(1)
        else:
            plugins_parser.print_help()
        return

    if args.command == "server":
        if args.server_command == "start":
            import uvicorn
            print(f"🐇 Starting Kanban Server on {args.host}:{args.port}")
            uvicorn.run("pyoco.server.api:app", host=args.host, port=args.port, log_level="info")
        return

    if args.command == "worker":
        if args.worker_command == "start":
            from ..worker.runner import Worker
            tags = args.tags.split(",") if args.tags else []
            worker = Worker(args.server, config, tags)
            worker.start()
        return

    if args.command == "runs":
        client = Client(args.server)
        try:
            if args.runs_command == "list":
                runs = client.list_runs(status=args.status, flow=args.flow, limit=args.limit)
                print(f"🐇 Active Runs ({len(runs)}):")
                print(f"{'ID':<36} | {'Status':<12} | {'Flow':<15}")
                print("-" * 70)
                for r in runs:
                    # RunContext doesn't have flow_name in core model, but store adds it.
                    # We need to access it safely.
                    flow_name = r.get("flow_name", "???")
                    print(f"{r['run_id']:<36} | {r['status']:<12} | {flow_name:<15}")
            
            elif args.runs_command == "show":
                run = client.get_run(args.run_id)
                print(f"🐇 Run: {run['run_id']}")
                print(f"Status: {run['status']}")
                print("Tasks:")
                for t_name, t_state in run.get("tasks", {}).items():
                    print(f"  [{t_state}] {t_name}")
            
            elif args.runs_command == "cancel":
                client.cancel_run(args.run_id)
                print(f"🛑 Cancellation requested for run {args.run_id}")
            elif args.runs_command == "inspect":
                run = client.get_run(args.run_id)
                if args.json:
                    print(json.dumps(run, indent=2))
                else:
                    print(f"🐇 Run: {run['run_id']} ({run.get('flow_name', 'n/a')})")
                    print(f"Status: {run['status']}")
                    if run.get("start_time"):
                        print(f"Started: {run['start_time']}")
                    if run.get("end_time"):
                        print(f"Ended: {run['end_time']}")
                    print("Tasks:")
                    records = run.get("task_records", {})
                    for name, info in records.items():
                        state = info.get("state", run["tasks"].get(name))
                        duration = info.get("duration_ms")
                        duration_str = f"{duration:.2f} ms" if duration else "-"
                        print(f"  - {name}: {state} ({duration_str})")
                        if info.get("error"):
                            print(f"      error: {info['error']}")
                    if not records:
                        for t_name, t_state in run.get("tasks", {}).items():
                            print(f"  - {t_name}: {t_state}")
            elif args.runs_command == "logs":
                _stream_logs(client, args)
        except Exception as e:
            print(f"Error: {e}")
        return

    if args.command == "run":
        flow_conf = config.flows.get(args.flow)
        if not flow_conf:
            print(f"Flow '{args.flow}' not found in config.")
            sys.exit(1)
        
        # Params
        params = flow_conf.defaults.copy()
        if args.param:
            for p in args.param:
                if "=" in p:
                    k, v = p.split("=", 1)
                    params[k] = v # Simple string parsing for now

        if args.server:
            # Remote execution
            client = Client(args.server)
            try:
                run_id = client.submit_run(args.flow, params)
                print(f"🚀 Flow submitted! Run ID: {run_id}")
                print(f"📋 View status: pyoco runs show {run_id} --server {args.server}")
            except Exception as e:
                print(f"Error submitting flow: {e}")
                sys.exit(1)
            return
        # Build Flow from graph string
        from ..dsl.syntax import TaskWrapper, switch
        eval_context = {name: TaskWrapper(task) for name, task in loader.tasks.items()}
        eval_context["switch"] = switch
        
        try:
            # Create Flow and add all loaded tasks
            flow = Flow(name=args.flow)
            for t in loader.tasks.values():
                flow.add_task(t)
            eval_context["flow"] = flow

            # Evaluate graph to set up dependencies
            exec(flow_conf.graph, {}, eval_context)
            
            # Run engine
            backend = ConsoleTraceBackend(style="cute" if args.cute else "plain")
            engine = Engine(trace_backend=backend)
            
            # Params (Moved up)
            
            # Signal handler for cancellation
            def signal_handler(sig, frame):
                print("\n🛑 Ctrl+C detected. Cancelling active runs...")
                for rid in list(engine.active_runs.keys()):
                    engine.cancel(rid)
            
            signal.signal(signal.SIGINT, signal_handler)
            
            engine.run(flow, params)
            
        except Exception as e:
            print(f"Error executing flow: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    elif args.command == "check":
        print(f"Checking flow '{args.flow}'...")
        flow_conf = config.flows.get(args.flow)
        if not flow_conf:
            print(f"Flow '{args.flow}' not found in config.")
            sys.exit(1)

        errors = []
        warnings = []

        # 1. Check imports (already done by loader.load(), but we can check for missing tasks in graph)
        # 2. Build flow to check graph
        from ..dsl.syntax import TaskWrapper, switch
        eval_context = {name: TaskWrapper(task) for name, task in loader.tasks.items()}
        eval_context["switch"] = switch
        
        try:
            flow = Flow(name=args.flow)
            for t in loader.tasks.values():
                flow.add_task(t)
            eval_context["flow"] = flow
            
            eval(flow_conf.graph, {}, eval_context)
            
            # 3. Reachability / Orphans
            if len(flow.tasks) > 1:
                for t in flow.tasks:
                    if not t.dependencies and not t.dependents:
                        warnings.append(f"Task '{t.name}' is orphaned (no dependencies or dependents).")

            # 4. Cycles
            visited = set()
            path = set()

            def visit(node):
                if node in path:
                    return True
                if node in visited:
                    return False
                visited.add(node)
                path.add(node)
                for dep in node.dependencies:
                    if visit(dep):
                        return True
                path.remove(node)
                return False
            
            for t in flow.tasks:
                if visit(t):
                    errors.append(f"Cycle detected involving task '{t.name}'.")
                    break

            # 5. Signature Check
            import inspect
            for t in flow.tasks:
                sig = inspect.signature(t.func)
                for name, param in sig.parameters.items():
                    if name == 'ctx': 
                        continue
                    if name not in t.inputs and name not in flow_conf.defaults:
                        warnings.append(f"Task '{t.name}' argument '{name}' might be missing input (not in inputs or defaults).")

        except Exception as e:
            errors.append(f"Graph evaluation failed: {e}")

        if args.dry_run:
            from ..dsl.validator import FlowValidator
            try:
                validator = FlowValidator(flow)
                dr_report = validator.validate()
                warnings.extend(dr_report.warnings)
                errors.extend(dr_report.errors)
            except Exception as exc:
                print(f"❌ Dry run internal error: {exc}")
                import traceback
                traceback.print_exc()
                sys.exit(3)

        status = "ok"
        if errors:
            status = "error"
        elif warnings:
            status = "warning"

        report = {"status": status, "warnings": warnings, "errors": errors}

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("\n--- Check Report ---")
            print(f"Status: {status}")
            if not errors and not warnings:
                print("✅ All checks passed!")
            else:
                for w in warnings:
                    print(f"⚠️  {w}")
                for e in errors:
                    print(f"❌ {e}")
        
        if errors:
            sys.exit(2 if args.dry_run else 1)
        return

def _collect_plugin_reports():
    dummy = SimpleNamespace(
        tasks={},
        discovery=SimpleNamespace(entry_points=[], packages=[], glob_modules=[]),
    )
    loader = TaskLoader(dummy)
    loader.load()
    return loader.plugin_reports


def _stream_logs(client, args):
    seen_seq = -1
    follow = args.follow
    while True:
        tail = args.tail if (args.tail and seen_seq == -1 and not follow) else None
        data = client.get_run_logs(args.run_id, task=args.task, tail=tail)
        logs = data.get("logs", [])
        logs.sort(key=lambda entry: entry.get("seq", 0))
        for entry in logs:
            seq = entry.get("seq", 0)
            if seq <= seen_seq:
                continue
            line = entry.get("text", "")
            line = line.rstrip("\n")
            print(f"[{entry.get('task', 'unknown')}][{entry.get('stream', '')}] {line}")
            seen_seq = seq
        status = data.get("run_status", "UNKNOWN")
        if not follow or status in ("COMPLETED", "FAILED", "CANCELLED"):
            if status == "FAILED" and not args.allow_failure:
                sys.exit(1)
            break
        time.sleep(1)


if __name__ == "__main__":
    main()

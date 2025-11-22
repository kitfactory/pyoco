import argparse
import sys
import os
from ..schemas.config import PyocoConfig
from ..discovery.loader import TaskLoader
from ..core.models import Flow
from ..core.engine import Engine
from ..trace.console import ConsoleTraceBackend

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

    # Check command
    check_parser = subparsers.add_parser("check", help="Verify a workflow")
    check_parser.add_argument("--config", required=True, help="Path to flow.yaml")
    check_parser.add_argument("--flow", default="main", help="Flow name to check")

    # List tasks command
    list_parser = subparsers.add_parser("list-tasks", help="List available tasks")
    list_parser.add_argument("--config", required=True, help="Path to flow.yaml")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load config
    try:
        config = PyocoConfig.from_yaml(args.config)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    # Discover tasks
    loader = TaskLoader(config)
    loader.load()

    if args.command == "list-tasks":
        print("Available tasks:")
        for name in loader.tasks:
            print(f" - {name}")
        return

    if args.command == "run":
        flow_conf = config.flows.get(args.flow)
        if not flow_conf:
            print(f"Flow '{args.flow}' not found in config.")
            sys.exit(1)
        
        # Build Flow from graph string
        from ..dsl.syntax import TaskWrapper
        eval_context = {name: TaskWrapper(task) for name, task in loader.tasks.items()}
        
        try:
            # Create Flow and add all loaded tasks
            flow = Flow(name=args.flow)
            for t in loader.tasks.values():
                flow.add_task(t)

            # Evaluate graph to set up dependencies
            exec(flow_conf.graph, {}, eval_context)
            
            # Run engine
            backend = ConsoleTraceBackend(style="cute" if args.cute else "plain")
            engine = Engine(trace_backend=backend)
            
            # Params
            params = flow_conf.defaults.copy()
            if args.param:
                for p in args.param:
                    if "=" in p:
                        k, v = p.split("=", 1)
                        params[k] = v # Simple string parsing for now
            
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
        from ..dsl.syntax import TaskWrapper
        eval_context = {name: TaskWrapper(task) for name, task in loader.tasks.items()}
        
        try:
            flow = Flow(name=args.flow)
            for t in loader.tasks.values():
                flow.add_task(t)
            
            eval(flow_conf.graph, {}, eval_context)
            
            # 3. Reachability / Orphans
            # Nodes with no deps and no dependents (except if single node flow)
            if len(flow.tasks) > 1:
                for t in flow.tasks:
                    if not t.dependencies and not t.dependents:
                        warnings.append(f"Task '{t.name}' is orphaned (no dependencies or dependents).")

            # 4. Cycles
            # Simple DFS for cycle detection
            visited = set()
            path = set()
            def visit(node):
                if node in path:
                    return True # Cycle
                if node in visited:
                    return False
                
                visited.add(node)
                path.add(node)
                for dep in node.dependencies: # Check upstream
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
                    if name == 'ctx': continue
                    # Check if input provided in task config or defaults
                    # This is hard because inputs are resolved at runtime.
                    # But we can check if 'inputs' mapping exists for it.
                    if name not in t.inputs and name not in flow_conf.defaults:
                        # Warning: might be missing input
                        warnings.append(f"Task '{t.name}' argument '{name}' might be missing input (not in inputs or defaults).")

        except Exception as e:
            errors.append(f"Graph evaluation failed: {e}")

        # Report
        print("\n--- Check Report ---")
        if not errors and not warnings:
            print("✅ All checks passed!")
        else:
            for w in warnings:
                print(f"⚠️  {w}")
            for e in errors:
                print(f"❌ {e}")
            
            if errors:
                sys.exit(1)

if __name__ == "__main__":
    main()

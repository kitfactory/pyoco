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
    # Allow overriding params via CLI? Spec doesn't explicitly say, but useful.

    # Check command
    check_parser = subparsers.add_parser("check", help="Verify a workflow")
    check_parser.add_argument("--config", required=True, help="Path to flow.yaml")

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
        # Use eval with tasks in context
        context = loader.tasks.copy()
        # We might need to wrap tasks to support DSL operators if they aren't already wrapped
        # But our TaskLoader returns Task objects.
        # Our DSL syntax relies on TaskWrapper or Task.__rshift__?
        # Task.__rshift__ is implemented in Task class? No, in TaskWrapper?
        # Wait, I put __rshift__ in TaskWrapper in dsl/syntax.py
        # But models.py Task class does NOT have __rshift__?
        # I should check models.py.
        
        # In models.py I did NOT add __rshift__ to Task.
        # So I need to wrap tasks in TaskWrapper for the eval to work with DSL.
        from ..dsl.syntax import TaskWrapper
        eval_context = {name: TaskWrapper(task) for name, task in loader.tasks.items()}
        
        try:
            # Create Flow and add all loaded tasks
            flow = Flow(name=args.flow)
            for t in loader.tasks.values():
                flow.add_task(t)

            # Evaluate graph to set up dependencies
            # The graph string is like "A >> (B & C)"
            eval(flow_conf.graph, {}, eval_context)
            
            # Run engine
            backend = ConsoleTraceBackend(style="cute" if args.cute else "plain")
            engine = Engine(trace_backend=backend)
            
            # Params
            params = flow_conf.defaults.copy()
            # TODO: CLI overrides
            
            engine.run(flow, params)
            
        except Exception as e:
            print(f"Error executing flow: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    elif args.command == "check":
        print("Check not fully implemented yet.")
        # TODO: Implement check logic
        pass

if __name__ == "__main__":
    main()

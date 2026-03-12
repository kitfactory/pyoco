# 8. Control & Observability

This chapter is about the parts you notice once a workflow is truly alive: identifying a run, watching it, and stopping it safely when needed.

Pyoco issues a unique **Run ID** for each execution and lets you safely **cancel** running workflows.

## 🎯 Goals

1.  Check the **Run ID**.
2.  Create a long-running task and cancel it with `Ctrl+C`.
3.  Use `ctx.is_cancelled` to implement Cooperative Cancellation in tasks.

## 🔎 1. Checking the Run ID

When you run Pyoco, the `run_id` is now displayed at the beginning of the log.

```bash
🐇 pyoco > start flow=my_flow run_id=a1b2c3d4-...
```

This ID is useful for log correlation and local debugging (server features are archived).

## 🧪 2. Creating a Cancellable Task

Long-running tasks should react to user cancellation requests (`Ctrl+C`) and interrupt their processing.
Pyoco informs tasks whether the current execution has been cancelled via the `ctx.is_cancelled` property.

Create `tasks.py`:

```python
import time
from pyoco import task

@task
def long_running_job(ctx):
    print("🏃 Starting long job...")
    
    for i in range(10):
        # Check for cancellation
        if ctx.is_cancelled:
            print("🛑 Cancellation detected! Cleaning up and exiting.")
            return "cancelled"
            
        print(f"⏳ Processing... {i+1}/10")
        time.sleep(1.0) # Simulate heavy work
        
    print("✅ Job completed")
    return "done"
```

Create `flow.yaml`:

```yaml
flow:
  graph: |
    long_running_job
  defaults: {}

tasks:
  long_running_job:
    callable: tasks:long_running_job
```

This local `callable` binding keeps the example easy to run. In a reusable package, expose the same task through a plug-in and bind it with `use`.

## ▶️ 3. Execution and Cancellation

Run this flow and press `Ctrl+C` halfway through.

```bash
pyoco run --config flow.yaml
```

**Example Output:**

```
🐇 pyoco > start flow=main run_id=...
🏃 start node=long_running_job
🏃 Starting long job...
⏳ Processing... 1/10
⏳ Processing... 2/10
^C
🛑 Ctrl+C detected. Cancelling active runs...
🛑 Cancellation detected! Cleaning up and exiting.
✅ done node=long_running_job (2015.32 ms)
🥕 done flow=main
```

### Explanation

1.  **Ctrl+C Detection**: The CLI receives `SIGINT` and requests cancellation from the engine.
2.  **Status Change**: The status of the execution context (`RunContext`) changes to `CANCELLING`.
3.  **Notification to Task**: `ctx.is_cancelled` in the task starts returning `True`.
4.  **Early Exit**: The task breaks the loop and exits. This prevents resource waste and allows for a safe shutdown.

If you do not check `ctx.is_cancelled`, the task will continue to run until completion (Pyoco does not perform forced termination). Implementing "Cooperative Cancellation" allows you to create well-behaved workflows.

## Summary

- You can identify executions with **Run ID**.
- You can cancel execution with **Ctrl+C**.
- You can implement processing (interruption, cleanup) in response to cancellation using **ctx.is_cancelled**.

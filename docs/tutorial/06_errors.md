# 6. Advanced: Error Handling

In this chapter, you will learn how to make your workflows robust against failures.

## Goal
- Configure retries for flaky tasks.
- Set timeouts for long-running tasks.
- Use failure policies (`fail_policy`).

## 1. Retries
If a task fails (raises an exception), Pyoco can automatically retry it.

```python
@task(retries=3)
def flaky_api_call(ctx):
    import random
    if random.random() < 0.7:
        raise ValueError("Network error!")
    return "Success"
```

Or in `flow.yaml`:
```yaml
tasks:
  flaky_api_call:
    retries: 3
```

## 2. Timeouts
You can limit how long a task is allowed to run.

```python
@task(timeout_sec=5.0)
def long_job(ctx):
    import time
    time.sleep(10) # This will fail!
```

## 3. Failure Policies
By default, if a task fails, the entire flow stops (`fail_policy="stop"`).
You can change this to `isolate` to allow independent tasks to continue.

```python
@task(fail_policy="isolate")
def non_critical_task(ctx):
    raise ValueError("Oops")
```

If `non_critical_task` fails:
- Tasks depending on it will be skipped.
- Independent tasks will continue to run.

This is useful for optional steps or parallel processing where one failure shouldn't crash the whole pipeline.

---
**Congratulations!** You have completed the Pyoco tutorial. You are now ready to build complex, robust, and cute workflows!

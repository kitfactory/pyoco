# 4. Parallelism & Branching

In this chapter, you will learn how to execute tasks in parallel and handle branching logic.

## Goal
- Execute independent tasks concurrently using `&`.
- Define branching logic using `|`.

## 1. Parallel Execution
Let's simulate a morning routine where you brush your teeth and wash your face at the same time (if you are multi-tasking!).

### `tasks.py`
```python
from pyoco.dsl.syntax import task
import time

@task
def brush_teeth(ctx):
    print("Brushing teeth...")
    time.sleep(1)
    return "teeth clean"

@task
def wash_face(ctx):
    print("Washing face...")
    time.sleep(1)
    return "face clean"

@task
def breakfast(ctx):
    print("Eating breakfast...")
    return "full"
```

### `flow.yaml`
```yaml
version: 1
discovery:
  glob_modules: ["tasks.py"]

flows:
  morning:
    graph: |
      (brush_teeth & wash_face) >> breakfast
```

- `(A & B)`: Defines a parallel group. Both tasks start simultaneously.
- `>> C`: Task C waits for **both** A and B to finish.

## 2. Branching (OR-Join)
Sometimes you only need one of the previous tasks to succeed to proceed.

```yaml
flows:
  flexible_morning:
    graph: |
      (brush_teeth | wash_face) >> breakfast
```

- `(A | B)`: Defines a branch.
- `>> C`: Task C waits for **any one** of A or B to finish. This is useful for "first-to-finish" or optional path scenarios.

## 3. Run It
Run the parallel flow:
```bash
pyoco run --config flow.yaml --flow morning --cute
```

You will see the tasks running together in the cute trace output!

[Next: Artifacts & Saving](05_artifacts.md)

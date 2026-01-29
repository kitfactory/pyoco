# 3. Data Flow & Dependencies

In this chapter, you will learn how to connect tasks together and pass data between them.

## Goal
- Define dependencies between tasks (`A >> B`).
- Pass the output of one task as input to another.

## 1. Define Tasks (`tasks.py`)
We'll create a pipeline that generates a number, multiplies it, and formats it.

```python
from pyoco.dsl.syntax import task
import random

@task
def generate_number(ctx):
    num = random.randint(1, 10)
    print(f"Generated: {num}")
    return num

@task
def multiply(ctx, value):
    result = value * 2
    print(f"Multiplied: {result}")
    return result

@task
def format_result(ctx, number):
    message = f"The final result is: {number}"
    print(message)
    return message
```

## 2. Configure Flow (`flow.yaml`)
We need to define the dependencies and map the inputs. The default pattern is to connect tasks via `$ctx.params`.

```yaml
version: 1

discovery:
  glob_modules:
    - "tasks.py"

tasks:
  generate_number:
    outputs:
      - "params.generated"
  multiply:
    inputs:
      # Prefer $ctx.params to connect tasks
      value: "$ctx.params.generated"
    outputs:
      - "params.multiplied"
  format_result:
    inputs:
      # Prefer $ctx.params to connect tasks
      number: "$ctx.params.multiplied"
    outputs:
      - "params.formatted"

flows:
  main:
    graph: |
      generate_number >> multiply >> format_result
```

- `>>`: Defines the execution order. `generate_number` runs first, then `multiply`, then `format_result`.
- `$ctx.params.<key>`: The standard way to connect tasks via shared parameters.
- Use `$node.<TaskName>.output` when you need to avoid overwriting shared params or require an explicit upstream output.

## 3. Run It
```bash
pyoco run --config flow.yaml
```

Output:
```
Generated: 5
Multiplied: 10
The final result is: 10
```

[Next: Parallelism & Branching](04_parallel.md)

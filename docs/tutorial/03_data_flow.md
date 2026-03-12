# 3. Data Flow & Dependencies

This chapter is where separate tasks start feeling like one workflow. You will connect outputs to downstream inputs and make the graph read like a story instead of isolated functions.

## 🎯 Goal
- Define dependencies between tasks (`A >> B`).
- Pass the output of one task as input to another.

## ✍️ 1. Define Tasks (`tasks.py`)
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

## 🗺️ 2. Configure Flow (`flow.yaml`)
We need to define the dependencies and map the inputs. The default pattern is to connect tasks via `$ctx.params`.

```yaml
version: 1

tasks:
  generate_number:
    callable: "tasks:generate_number"
    outputs:
      - "params.generated"
  multiply:
    callable: "tasks:multiply"
    inputs:
      # Prefer $ctx.params to connect tasks
      value: "$ctx.params.generated"
    outputs:
      - "params.multiplied"
  format_result:
    callable: "tasks:format_result"
    inputs:
      # Prefer $ctx.params to connect tasks
      number: "$ctx.params.multiplied"
    outputs:
      - "params.formatted"

flow:
  graph: |
    generate_number >> multiply >> format_result
```

- `>>`: Defines the execution order. `generate_number` runs first, then `multiply`, then `format_result`.
- `$ctx.params.<key>`: The standard way to connect tasks via shared parameters.
- Use `$node.<TaskName>.output` when you need to avoid overwriting shared params or require an explicit upstream output.
- This chapter still uses local `callable` bindings for brevity. Once the tasks are reusable, move the same graph idea to plug-ins + `tasks.<local>.use`.

## ▶️ 3. Run It
```bash
pyoco run --config flow.yaml
```

Output:
```
Generated: 5
Multiplied: 10
The final result is: 10
```

If Chapter 2 made the flow configurable, this chapter makes it composable. The next step is to add branching and loops without losing readability.

[Next: Control Components (pipe/switch/repeat/foreach/until)](04_parallel.md)

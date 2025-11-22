# 2. Parameters & Inputs

In this chapter, you will learn how to make your tasks dynamic by using parameters and inputs.

## Goal
- Pass parameters to tasks from the configuration.
- Override parameters from the command line.

## 1. Update `tasks.py`
Modify `tasks.py` to accept arguments:

```python
from pyoco.dsl.syntax import task

@task
def greet(ctx, name, greeting="Hello"):
    print(f"{greeting}, {name}!")
```

- Pyoco automatically injects parameters if their names match the function arguments.

## 2. Update `flow.yaml`
Update `flow.yaml` to define default parameters:

```yaml
version: 1

discovery:
  glob_modules:
    - "tasks.py"

flows:
  main:
    defaults:
      name: "User"
      greeting: "Hi"
    graph: |
      greet
```

- `defaults`: Sets global default values for parameters.

## 3. Run with Defaults
Run the flow as before:

```bash
pyoco run --config flow.yaml
```

Output:
```
Hi, User!
```

## 4. Override via CLI
You can override parameters using the `--param` flag:

```bash
pyoco run --config flow.yaml --param name=Alice --param greeting=Welcome
```

Output:
```
Welcome, Alice!
```

This makes your workflows reusable for different contexts without changing the code.

## 5. Advanced Selectors
You can also access context parameters and environment variables directly in your `flow.yaml` using selectors.

### Context Parameters (`$ctx.params`)
Instead of relying on auto-injection, you can explicitly map parameters:

```yaml
tasks:
  greet:
    inputs:
      name: "$ctx.params.name"
```

### Environment Variables (`$env`)
You can access environment variables using `$env`:

```yaml
tasks:
  api_call:
    inputs:
      api_key: "$env.API_KEY"
```

[Next: Data Flow & Dependencies](03_data_flow.md)

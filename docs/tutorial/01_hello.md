# 1. Hello World

In this chapter, you will create and run your very first Pyoco workflow.

## Goal
- Create a simple task that prints "Hello, Pyoco!".
- Define a workflow configuration.
- Run the workflow using the CLI.

## 1. Project Structure
Create a new directory for your project (e.g., `my_first_flow`) and create two files:
- `tasks.py`: Contains your Python code.
- `flow.yaml`: Defines the workflow structure.

## 2. Define a Task (`tasks.py`)
Open `tasks.py` and add the following code:

```python
from pyoco.dsl.syntax import task

@task
def hello(ctx):
    print("Hello, Pyoco!")
    return "done"
```

- The `@task` decorator marks the function as a Pyoco task.
- The `ctx` argument is the context object, which allows access to parameters and other features (we'll use it later).

## 3. Configure the Flow (`flow.yaml`)
Open `flow.yaml` and define your workflow:

```yaml
version: 1

# Tell Pyoco where to find your tasks
discovery:
  glob_modules:
    - "tasks.py"

# Define the flow
flows:
  main:
    graph: |
      hello
```

- `discovery`: Points to your python file.
- `flows`: Defines a flow named `main`.
- `graph`: A simple string listing the tasks to run. Here, just `hello`.

## 4. Run It!
Open your terminal and run:

```bash
pyoco run --config flow.yaml
```

You should see output similar to:

```
🐇 pyoco > start flow=main
🏃 start node=hello
Hello, Pyoco!
✅ done node=hello (0.05 ms)
🥕 done flow=main
```

Congratulations! You've just run your first Pyoco workflow.

[Next: Parameters & Inputs](02_params.md)

# Pyoco Documentation

Welcome to the documentation for **Pyoco**, a workflow engine with sugar syntax.

## Getting Started

### Installation

```bash
uv add pyoco
```

### Basic Usage

```python
from pyoco import task, workflow

@task
def step1():
    print("Step 1")

@task
def step2():
    print("Step 2")

with workflow("my_workflow") as wf:
    step1() >> step2()

wf.run()
```

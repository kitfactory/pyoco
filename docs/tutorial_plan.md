# Pyoco Tutorial Curriculum

This document outlines the proposed step-by-step tutorial to help users master `pyoco`.

## 1. Hello World (`01_hello`)
**Goal**: Run your first workflow.
- **Concepts**:
    - Directory structure (`tasks.py`, `flow.yaml`).
    - Defining a simple `@task`.
    - Basic `flow.yaml` configuration.
    - Running with `pyoco run`.
- **Scenario**: A simple task that prints "Hello, Pyoco!".

## 2. Parameters & Inputs (`02_params`)
**Goal**: Make tasks dynamic with parameters.
- **Concepts**:
    - Defining `defaults` in `flow.yaml`.
    - Overriding parameters via CLI (`--param`).
    - Accessing parameters in tasks (auto-injection).
- **Scenario**: A generic greeting task that takes `name` and `greeting` as parameters.

## 3. Data Flow & Dependencies (`03_data_flow`)
**Goal**: Connect tasks and pass data between them.
- **Concepts**:
    - Defining dependencies: `TaskA >> TaskB`.
    - Returning values from tasks.
    - Mapping inputs using selectors: `$node.TaskA.output`.
- **Scenario**:
    - Task 1: Generates a random number.
    - Task 2: Multiplies it by 2.
    - Task 3: Formats the result string.

## 4. Parallelism & Branching (`04_parallel`)
**Goal**: Execute tasks concurrently and handle logic branches.
- **Concepts**:
    - Parallel execution syntax: `(A & B)`.
    - Branching syntax: `(A | B)`.
    - Understanding "Cute Mode" output for parallel tasks.
- **Scenario**:
    - "Morning Routine": Brush teeth and Wash face (Parallel).
    - Then: Eat breakfast.

## 5. Artifacts & Saving (`05_artifacts`)
**Goal**: Persist task outputs to files.
- **Concepts**:
    - The `save:` configuration.
    - `ctx.save_artifact()` method.
    - Viewing generated artifacts.
- **Scenario**: Generate a report text and save it as `report.txt`.

## 6. Advanced: Error Handling (`06_errors`)
**Goal**: Build robust workflows.
- **Concepts**:
    - `retries`.
    - `fail_policy="isolate"`.
    - `timeout_sec`.
- **Scenario**: A "flaky" network request task that retries and eventually succeeds (or fails safely).

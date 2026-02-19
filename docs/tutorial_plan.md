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

## 4. Control Components (`04_parallel`)
**Goal**: Compose control flow with current graph DSL components.
- **Concepts**:
    - `pipe(NAME)` for reusable pipeline fragments.
    - `switch(on=...){ ... }` for single-branch selection.
    - `repeat` / `foreach` / `until` for loop control.
- **Scenario**:
    - Setup pipeline via `pipe(setup)`.
    - Route by mode with `switch`.
    - Process list items with `foreach` and poll completion with `until`.

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

## 7. Custom Tasks (`07_custom_tasks`)
**Goal**: Create reusable, structured tasks using `BaseTask`.
- **Concepts**:
    - Subclassing `BaseTask`.
    - Implementing `run(self, ctx)`.
    - Sharing logic between tasks.
- **Scenario**: A custom multiplication task that inherits from a base class.

## 8. Control & Observability (`08_control`)
**Goal**: Manage and monitor long-running workflows.
- **Concepts**:
    - **Run ID**: Identifying specific executions.
    - **Cancellation**: Stopping a flow with `Ctrl+C`.
    - **Cooperative Cancellation**: Using `ctx.is_cancelled` in long tasks.
- **Scenario**: A long-running "simulation" task that can be safely interrupted by the user.

# v0.3.0 Walkthrough: Kanban Server & Workers

This release introduces asynchronous execution capabilities with a Kanban Server and Workers, enabling remote workflow submission and management.

## New Features

### 1. Kanban Server
A lightweight FastAPI server that manages run state and queues.

**Start the server:**
```bash
pyoco server start --port 8000
```

### 2. Workers
Workers pull jobs from the server and execute them. They now support "Cute" trace output in their logs!

**Start a worker:**
```bash
pyoco worker start --server http://localhost:8000 --config flow.yaml
```

### 3. Remote Execution
Submit flows to the server instead of running locally.

**Submit a run:**
```bash
pyoco run --config flow.yaml --flow my_flow --server http://localhost:8000
# 🚀 Flow submitted! Run ID: ...
```

### 4. Observability & Control
Manage runs via the CLI.

**List runs:**
```bash
pyoco runs list --server http://localhost:8000
```

**Show run details:**
```bash
pyoco runs show <run_id> --server http://localhost:8000
```

**Cancel a run:**
```bash
pyoco runs cancel <run_id> --server http://localhost:8000
```

## Verification
We verified the implementation with a full integration test (`tests/test_integration_v030.py`) covering:
- Server startup and API availability.
- Worker connection and polling.
- Remote run submission.
- Execution success and status updates.
- Remote cancellation.

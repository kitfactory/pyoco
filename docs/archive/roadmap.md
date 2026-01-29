# 🗺️ Pyoco Roadmap

pyoco is intentionally small. This roadmap describes how it may grow while staying minimal, with a focus on observability and UI-readiness.

## Execution Lifecycle Overview

Pyoco's execution model is designed for simplicity and observability.

- **Ephemeral**: Flow executions are transient.
- **No Resume**: We do not support resuming failed workflows from the middle. Task contexts are not serialized.
- **Cancellable**: Users can stop execution at any time.
- **Observable**: We prioritize knowing "what is happening now" over "how to recover later".

## 🎭 Trace Modes

Pyoco supports two output modes, compatible with future UI layers:

- **Cute Mode** (Default): Friendly logs with emojis.
- **Non-Cute Mode**: Operational logs for CI/CD.

## Step 1: Basic Flow Execution & Trace (local synchronous) - v0.1.0

**Goal:** Make pyoco run small workflows in a single process with readable trace output.

**Features:**
- DAG model (`Task`, `Flow`)
- Synchronous execution only
- Simple trace logging (cute / non-cute)
- No RunId
- No state query API
- No cancel API

**What will NOT be implemented here:**
- No persistence
- No resume
- No worker model

## Step 2: RunContext, RunId, and TaskState (local) - v0.2.0

**Goal:** Introduce an explicit execution context and observable state model. This enables "Where is the workflow now?" queries.

**Add:**
1. **RunContext** ✅
   - `run_id` ✅
   - `run_status` = `RUNNING / COMPLETED / FAILED` ✅
   - Internal dict of task states ✅
2. **TaskState enum** ✅
   - `PENDING` ✅
   - `RUNNING` ✅
   - `SUCCEEDED` ✅
   - `FAILED` ✅
   - (prepare only) `CANCELLED` ✅
3. **State query API** ✅
   - Python API: `handle.status()`, `handle.tasks()` (via Engine/Context) ✅
   - CLI: `pyoco runs list`, `pyoco runs show <run_id>` (Trace output shows ID) ✅

**Not included yet:**
- Cancel
- Queue
- Persistence

## Step 3: Cancellation Model (Stop Without Resume) - v0.2.0

**Goal:** Allow users to stop an in-progress workflow at any time. Resume is explicitly **not supported**.

**Add:**
1. **Cancel API** ✅
   - `flow.cancel(run_id)` ✅
   - Sets `run_status` = `CANCELLING → CANCELLED` ✅
2. **Effect of cancellation** ✅
   - New tasks will not start ✅
   - Pending tasks become `CANCELLED` ✅
   - Running tasks finish naturally (no forced kill) ✅
3. **Cooperative cancellation support** ✅
   - Introduce `TaskContext` (Updated Context) ✅
   - `ctx.cancelled` is available (`ctx.is_cancelled`) ✅
   - Long-running tasks may choose to exit early ✅

**UI benefit:** The "Stop" button will work cleanly.

## Step 4: Local Queue Execution (single-machine), Lightweight StateStore - v0.3.0

**Goal:** Move from synchronous execution to a queued execution model without introducing distributed components.

**Add:**
1. **QueueBackend (in-memory)** ✅
   - `enqueue(run_id, task_id, ...)` ✅
   - `dequeue()` for a local worker loop ✅
2. **Local Worker** ✅
   - Single-thread worker pulling from the queue ✅
   - Honors cancellation (skips cancelled runs, removes cancelled tasks) ✅
3. **StateStore abstraction** ✅
   - In-memory version (default) ✅
   - Lightweight persistent version (JSONL or SQLite) for observability only (Skipped for now)
4. **CLI: queue-aware introspection** ✅
   - `pyoco runs show <run_id>` shows queued, running, succeeded, failed, cancelled ✅

**Not implemented here:**
- Multi-process
- Distributed execution
- Resume

## Step 5: Kanban Server & Workers (Multi-process / future-proof) - v0.3.0

**Goal:** Introduce a lightweight central server for queue management, state persistence, observability, and remote cancellation.

**Add:**
1. **Kanban Server components** ✅
   - Run registry ✅
   - Task registry (state + timestamps) ✅
   - Queue backend ✅
   - State backend ✅
2. **API** ✅
   - `POST /runs` ✅
   - `GET /runs/<id>` ✅
   - `GET /runs/<id>/tasks` (Included in GET /runs/<id>) ✅
   - `POST /runs/<id>/cancel` ✅
3. **Workers** ✅
   - `pyoco worker --server <url>` ✅
   - Pulls tasks from server queue ✅
   - Updates server-side TaskState ✅
   - Respects cancellation ✅
4. **CLI** ✅
   - `pyoco runs list` ✅
   - `pyoco runs show <id>` ✅
   - `pyoco runs cancel <id>` ✅

**Explicit non-goals:**
- Resume (no task context serialization)
- Distributed orchestration on multiple nodes
- Heavy scheduler logic (Airflow-like)

## UI-Oriented Rationale

This roadmap ensures Pyoco is ready for a future UI layer:

- **Run List** maps directly to `RunContext`.
- **DAG View** maps directly to `TaskState`.
- **Queue View** maps directly to `QueueBackend`.
- **Stop Button** maps directly to the cancellation API.
- **History** maps directly to `StateStore`.

## Non-Goals

- **pyoco does not implement restart/resume of workflows.**
- **pyoco never serializes task execution context.**
- **pyoco focuses on observability (read-only) rather than recoverability.**
- **pyoco is intentionally minimal and non-invasive.**

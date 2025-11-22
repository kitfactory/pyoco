# 🗺️ Pyoco Roadmap

pyoco is intentionally small. This roadmap describes how it may grow while staying minimal.

## Phase 1: Local, single-process DAG runner (Current)

Focus on defining and running small DAGs in a single process.

- **Features**:
    - [x] Task dependencies (`>>`)
    - [x] Simple retries and timeouts
    - [x] Cute/Plain trace logs
    - [x] Artifact management
- **Non-goals**:
    - Web UI (Use CLI trace instead)

## Phase 2: Single-machine concurrency & simple queue

Introduce parallel execution and simple queuing within a single machine.

- **Features**:
    - [x] Parallel execution (ThreadPoolExecutor)
    - [ ] Worker count configuration
    - [ ] Simple in-memory or file-based queue for task ordering
- **Non-goals**:
    - Multi-node distributed execution (Keep it single-machine)

## Phase 3: Kanban-style server & pluggable backends

Introduce a "Kanban server" to manage small jobs as cards, suitable for slightly larger local operations.

- **Concept**:
    - Treat small jobs as "cards" on a board.
    - A lightweight server component manages the state of these cards.
- **Features**:
    - [ ] Built-in lightweight server (no external DB required)
    - [ ] Pluggable backends for queue/state (Redis, RabbitMQ) for those who need it.
    - [ ] `pyoco worker` command to pull tasks from the queue.
- **Non-goals**:
    - Complex enterprise scheduling features (unless via plugins)
    - Heavy default dependencies (Redis/DB should remain optional)

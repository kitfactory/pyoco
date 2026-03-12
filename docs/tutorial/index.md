# 🐇 Pyoco Tutorial

Welcome. This tutorial is meant to get you to a small win fast, then show you the model Pyoco actually wants you to keep using.

## ✨ How To Read This Tutorial

- ⚡ Want the fastest success? Read Chapter 1 first and run it as-is.
- 🧩 Want the recommended project shape? Read Chapter 1, then jump to Chapter 7.
- 🛠️ Want the full graph DSL? Read straight through from Chapter 1 to Chapter 4.

Default recommendation: package reusable tasks as **entry point plug-ins** and bind their public names in `flow.yaml` with `tasks.<local_name>.use`. Some early chapters still use `tasks.<name>.callable` because it keeps single-file examples short.

## 📚 Table of Contents

1.  [Hello World](01_hello.md)
    *   Get your first Pyoco run in a few minutes.
2.  [Parameters & Inputs](02_params.md)
    *   Make your workflow feel less like a demo and more like a tool.
3.  [Data Flow & Dependencies](03_data_flow.md)
    *   Pass results between tasks and keep the graph readable.
4.  [Control Components (pipe/switch/repeat/foreach/until)](04_parallel.md)
    *   Add branching, reuse, and loops to the graph DSL.
5.  [Artifacts & Saving](05_artifacts.md)
    *   Save outputs when the workflow needs to leave traces behind.
6.  [Advanced: Error Handling](06_errors.md)
    *   Add retries and limits so the flow survives rough edges.
7.  [Custom Tasks with BaseTask](07_custom_tasks.md)
    *   Learn the recommended reusable-task path: `BaseTask` + plug-ins + `use`.
8.  [Control & Observability](08_control.md)
    *   Inspect run IDs and stop workflows cleanly with Ctrl+C.

---
[日本語版 (Japanese Version)](index_ja.md)

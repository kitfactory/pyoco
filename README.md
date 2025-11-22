# 🐇 Pyoco

**The cutest workflow engine for Python.** ✨

Pyoco is a lightweight, developer-friendly workflow engine designed to make your data pipelines and automation tasks not just functional, but *delightful*.

With a focus on simplicity and developer experience, Pyoco brings a touch of magic to your daily coding.

## ✨ Features

- **🍰 Simple DSL**: Define tasks with a simple `@task` decorator and connect them with `>>`.
- **🐇 Cute Output**: Enjoy beautiful, emoji-rich console logs that make debugging a joy.
- **🚀 Parallel Execution**: Automatically runs independent tasks in parallel.
- **🛡️ Robust**: Built-in support for retries, timeouts, and failure handling policies.
- **📦 Artifact Management**: Easily save and manage task outputs and files.

## 📦 Installation

```bash
pip install pyoco
```

## 🚀 Quick Start

Create a file named `tasks.py`:

```python
from pyoco import task

@task
def hello(ctx):
    print("Hello, Pyoco! 🐇")
    return "World"

@task
def greet(ctx, name):
    print(f"Nice to meet you, {name}! ✨")
```

Create a `flow.yaml`:

```yaml
version: 1
discovery:
  glob_modules: ["tasks.py"]

tasks:
  greet:
    inputs:
      name: "$node.hello.output"

flows:
  main:
    graph: |
      hello >> greet
```

Run it!

```bash
pyoco run --config flow.yaml
```

You'll see:

```
🐇 pyoco > start flow=main
🏃 start node=hello
Hello, Pyoco! 🐇
✅ done node=hello (0.12 ms)
🏃 start node=greet
Nice to meet you, World! ✨
✅ done node=greet (0.08 ms)
🥕 done flow=main
```

## 📚 Documentation

- [Tutorials](docs/tutorial/index.md)
- [Roadmap](docs/roadmap.md)

## 💖 Contributing

We love contributions! Please feel free to submit a Pull Request.

---

*Made with 🥕 by the Pyoco Team.*

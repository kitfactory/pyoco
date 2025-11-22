import subprocess
import time
import signal
import os
import sys

def test_cli_cancellation():
    # Create a slow flow
    flow_yaml = """
flows:
  slow_flow:
    graph: |
      slow_task
    defaults: {}

tasks:
  slow_task:
    callable: tasks:slow_task
"""
    
    tasks_py = """
import time
from pyoco import task

@task
def slow_task(ctx):
    print("Slow task started")
    for i in range(100):
        if ctx.is_cancelled:
            print("Slow task cancelled!")
            return "cancelled"
        time.sleep(0.1)
    return "finished"
"""

    with open("flow_cancel.yaml", "w") as f:
        f.write(flow_yaml)
    with open("tasks.py", "w") as f:
        f.write(tasks_py)

    # Run CLI
    cmd = [sys.executable, "src/pyoco/cli/entry.py", "run", "--config", "flow_cancel.yaml", "--flow", "slow_flow"]
    env = os.environ.copy()
    env["PYTHONPATH"] = "src:."
    
    print(f"Running command: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd, 
        env=env, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1 # Line buffered
    )

    try:
        # Wait for start (just sleep 2 seconds)
        time.sleep(2)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print("Process exited too early!")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            sys.exit(1)

        print("Sending SIGINT...")
        process.send_signal(signal.SIGINT)
        
        # Wait for exit
        try:
            stdout, stderr = process.communicate(timeout=5)
            print("Process exited gracefully.")
        except subprocess.TimeoutExpired:
            print("Process did not exit in time!")
            process.kill()
            stdout, stderr = process.communicate()
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            sys.exit(1)

        print("STDOUT:", stdout)
        
        if "Ctrl+C detected" in stdout and "Slow task cancelled!" in stdout:
            print("SUCCESS: Cancellation verified.")
        else:
            print("FAILURE: Cancellation message not found.")
            sys.exit(1)

    finally:
        if process.poll() is None:
            process.kill()
        
        # Cleanup
        if os.path.exists("flow_cancel.yaml"):
            os.remove("flow_cancel.yaml")
        if os.path.exists("tasks.py"):
            os.remove("tasks.py")

if __name__ == "__main__":
    test_cli_cancellation()

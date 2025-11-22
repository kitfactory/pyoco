from pyoco import task
from pyoco.core.models import Flow
from pyoco.core.engine import Engine

@task
def fetch_data(ctx):
    print("🐰 Fetching data...")
    return {"id": 1, "value": "carrot"}

@task
def process_data(ctx, data):
    print(f"🥕 Processing: {data['value']}")
    return data['value'].upper()

@task
def save_result(ctx, result):
    print(f"✨ Saved: {result}")

# Define the flow
flow = Flow(name="hello_pyoco")
flow >> fetch_data >> process_data >> save_result

# Configure inputs (simple wiring)
# In a pure python script, we can wire inputs manually if needed, 
# or rely on context if we implemented auto-wiring based on return values.
# For this simple example, let's use the context explicitly or rely on the engine's auto-wiring if supported.
# Current engine implementation supports auto-wiring from ctx.results if parameter name matches task name?
# Let's check Engine._execute_task.
# It checks: if param_name in ctx.results.
# So if 'process_data' takes 'data', and 'fetch_data' returns something, we need to map it.
# Or we can use `inputs` on the task object.

# Let's wire it explicitly for clarity in this script
process_data.task.inputs = {"data": "$node.fetch_data.output"}
save_result.task.inputs = {"result": "$node.process_data.output"}

if __name__ == "__main__":
    engine = Engine()
    engine.run(flow)

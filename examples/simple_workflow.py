from pyoco import task, workflow

@task
def load_data():
    print("Loading data...")
    return "data"

@task
def process_data(data):
    print(f"Processing {data}...")
    return "processed_data"

@task
def save_data(data):
    print(f"Saving {data}...")

with workflow("my_first_workflow") as wf:
    # Define dependencies
    # Note: We call the tasks to register them and capture args (if any)
    t1 = load_data()
    t2 = process_data("raw_data")
    t3 = save_data("processed_data")
    
    t1 >> t2 >> t3

if __name__ == "__main__":
    print("Running workflow...")
    wf.run()

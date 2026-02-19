from pyoco import task, Flow, run

@task
def A(ctx, x:int)->int: 
    print(f"Executing A with x={x}")
    return x+1

@task
def B(ctx, x:int)->int: 
    print(f"Executing B with x={x}")
    return x*2

@task
def C(ctx, x:int)->int: 
    print(f"Executing C with x={x}")
    return x-3

flow = Flow() >> A >> B >> C

if __name__ == "__main__":
    print("--- Running in Cute Mode ---")
    res = run(flow, params={"x":1}, trace=True, cute=True)
    print("Context Results:", res.results)
    
    print("\n--- Running in Plain Mode ---")
    res = run(flow, params={"x":1}, trace=True, cute=False)

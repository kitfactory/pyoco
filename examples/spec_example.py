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

# Note: In the spec, inputs are resolved from context or previous outputs.
# Our current simple engine implementation tries to resolve 'x' from params or results.
# But B and C depend on A. A returns a value.
# We need to ensure that B and C get A's output as 'x'.
# The spec YAML example shows: inputs: x: $node.A.output
# For Python API, we might need a way to specify this mapping or rely on parameter names matching node names (which they don't here: 'x' vs 'A').
# However, for this MVP verification, let's see if we can just pass 'x' from params for A,
# and for B/C, we might need to adjust the example or the engine logic to auto-wire if possible,
# or just accept that for now they might fail or use the same 'x' if not wired.
#
# WAIT, the spec Python API example:
# flow = Flow() >> A >> (B & C)
# run(flow, params={"x":1})
#
# It implies implicit data passing or just execution order.
# If B needs 'x', and 'x' is in params, it uses params['x'].
# If B needs result of A, it's not explicitly stated in the Python API example how data flows *without* the YAML 'inputs' mapping.
# Unless... the return value of A is automatically stored in ctx.results['A'].
# And if B had an argument named 'A', it would get it. But it has 'x'.
#
# Let's assume for this test that we just want to verify execution order and trace output.
# We can adjust the functions to not strictly depend on A's output for now, or we can try to make it work.

flow = Flow() >> A >> (B & C)

if __name__ == "__main__":
    print("--- Running in Cute Mode ---")
    res = run(flow, params={"x":1}, trace=True, cute=True)
    print("Context Results:", res.results)
    
    print("\n--- Running in Plain Mode ---")
    res = run(flow, params={"x":1}, trace=True, cute=False)

from pyoco import task

@task
def A(ctx, x:int=0):
    print(f"Task A: x={x}")
    return x + 1

@task
def B(ctx, x:int=0):
    print(f"Task B: x={x}")
    return x * 2

@task
def C(ctx, x:int=0):
    print(f"Task C: x={x}")
    return x - 3

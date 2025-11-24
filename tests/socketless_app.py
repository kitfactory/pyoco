from fastapi import FastAPI

app = FastAPI()

STATE = {"count": 0}


@app.get("/hello")
async def hello():
    STATE["count"] += 1
    return {"message": "hello", "count": STATE["count"]}


def reset_state():
    STATE["count"] = 0

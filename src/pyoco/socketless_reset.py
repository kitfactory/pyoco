from pyoco.server.api import store


def reset_store():
    store.runs.clear()
    store.queue.clear()
    store.history.clear()

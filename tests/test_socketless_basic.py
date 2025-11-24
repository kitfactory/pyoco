import httpx
import pytest
from socketless_http import reset_ipc_state, switch_to_ipc_connection


@pytest.fixture(scope="module", autouse=True)
def socketless_session():
    cleanup = switch_to_ipc_connection(
        "tests.socketless_app:app",
        reset_hook="tests.socketless_app:reset_state",
        base_url="http://testserver",
        debug=True,
    )
    yield
    cleanup()


@pytest.fixture(autouse=True)
def reset_state():
    reset_ipc_state()


def test_socketless_hello_roundtrip():
    client = httpx.Client()
    resp = client.get("/hello")
    assert resp.status_code == 200
    assert resp.json() == {"message": "hello", "count": 1}
    resp2 = client.get("/hello")
    assert resp2.json() == {"message": "hello", "count": 2}

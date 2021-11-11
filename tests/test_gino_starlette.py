import asyncio

import pytest
from starlette.testclient import TestClient


def _test_index_returns_200(app):
    client = TestClient(app)
    with client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.text == "Hello, world!"


def test_index_returns_200(app):
    _test_index_returns_200(app)


def test_index_returns_200_dsn(app_dsn):
    _test_index_returns_200(app_dsn)


def _test(app):
    client = TestClient(app)
    with client:
        for method in "01234":
            response = client.get("/users/1?method=" + method)
            assert response.status_code == 404

        response = client.post("/users", json=dict(name="fantix"))
        assert response.status_code == 200
        assert response.json() == dict(id=1, nickname="fantix")

        for method in "01234":
            response = client.get("/users/1?method=" + method)
            assert response.status_code == 200
            assert response.json() == dict(id=1, nickname="fantix")


def test(app):
    _test(app)


def test_ssl(app_ssl):
    _test(app_ssl)


def test_dsn(app_dsn):
    _test(app_dsn)


def test_app_factory(app_factory):
    _test(app_factory)


"""
disable this test for now because latest Starlette TestClient is using anyio to
manage event loop, which is in another blocking thread. This call_later is not
invoked until that is terminated.

def test_db_delayed(app_db_delayed):
    loop = asyncio.get_event_loop()
    loop.call_later(1, loop.create_task, app_db_delayed.start_proxy())
    client = TestClient(app_db_delayed)
    with client:
        pass
"""


def test_no_db(app_db_delayed):
    client = TestClient(app_db_delayed)
    with pytest.raises(Exception):
        with client:
            pass

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

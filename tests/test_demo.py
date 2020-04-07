import uuid


def test(venv_client):
    assert venv_client.get("/users/1").status_code == 404
    nickname = str(uuid.uuid4())
    r = venv_client.post("/users", json=dict(name=nickname))
    r.raise_for_status()
    r = r.json()
    assert (
        venv_client.get("/users/{}".format(r["id"])).json()["nickname"]
        == nickname
    )

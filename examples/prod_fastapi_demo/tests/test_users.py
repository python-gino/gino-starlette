import uuid


def test_crud(client):
    assert client.get("/users/1").status_code == 404
    nickname = str(uuid.uuid4())
    r = client.post("/users", json=dict(name=nickname))
    r.raise_for_status()
    r = r.json()
    assert (
        client.get("/users/{}".format(r["id"])).json()["nickname"] == nickname
    )

import uuid


def test_crud(client):
    # create
    nickname = str(uuid.uuid4())
    r = client.post("/users", json=dict(name=nickname))
    r.raise_for_status()

    # retrieve
    url = "/users/{}".format(r.json()['id'])
    assert client.get(url).json()["nickname"] == nickname

    # delete
    client.delete(url).raise_for_status()
    assert client.get(url).status_code == 404

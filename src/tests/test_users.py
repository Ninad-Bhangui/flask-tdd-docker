import json

import pytest

from src.api.models import User


def test_add_user(test_app, test_database):
    client = test_app.test_client()
    resp = client.post(
        "/users",
        data=json.dumps({"username": "john", "email": "john@seven.io"}),
        content_type="application/json",
    )

    data = json.loads(resp.data.decode())
    assert resp.status_code == 201
    assert "john@seven.io was added!" in data["message"]


def test_add_user_invalid_json(test_app, test_database):
    client = test_app.test_client()
    resp = client.post(
        "/users",
        data=json.dumps(
            {
                "email": "john@seven.io",
            }
        ),
        content_type="application/json",
    )
    data = json.loads(resp.data.decode())
    assert resp.status_code == 400
    assert "Input payload validation failed" in data["message"]


def test_add_user_duplicate_email(test_app, test_database):
    client = test_app.test_client()
    resp = client.post(
        "/users",
        data=json.dumps({"username": "john", "email": "john@seven.io"}),
        content_type="application/json",
    )
    data = json.loads(resp.data.decode())
    assert resp.status_code == 400
    assert "Sorry. That email already exists." in data["message"]


def test_single_user(test_app, test_database, add_user):
    user = add_user("william", "william@seven.io")
    client = test_app.test_client()
    resp = client.get(f"/users/{user.id}")
    data = json.loads(resp.data.decode())
    print(data)
    assert resp.status_code == 200
    assert "william" in data["username"]


def test_single_user_incorrect_id(test_app, test_database):
    client = test_app.test_client()
    resp = client.get("/users/999")
    data = json.loads(resp.data.decode())
    assert resp.status_code == 404
    assert "User 999 does not exist" in data["message"]


def test_all_users(test_app, test_database, add_user):
    test_database.session.query(User).delete()
    add_user("john", "johndoe@seven.org")
    add_user("david", "davidmills@seven.com")
    client = test_app.test_client()
    resp = client.get("/users")
    data = json.loads(resp.data.decode())
    assert resp.status_code == 200
    assert len(data) == 2
    assert "john" in data[0]["username"]
    assert "johndoe@seven.org" in data[0]["email"]
    assert "david" in data[1]["username"]


def test_remove_user(test_app, test_database, add_user):
    test_database.session.query(User).delete()
    user = add_user("deluser", "deluser@seven.org")
    client = test_app.test_client()
    resp = client.delete(f"/users/{user.id}")
    data = json.loads(resp.data.decode())
    assert resp.status_code == 200
    assert "deluser was removed" in data["message"]

    test_database.session.remove()  # To make sure the test fails if session commit is forgotten in code
    del_user = User.query.filter_by(id=user.id).first()
    assert del_user is None

    resp_two = client.get(f"/users/{user.id}")
    assert resp_two.status_code == 404


def test_remove_invalid_user(test_app, test_database, add_user):
    test_database.session.query(User).delete()
    client = test_app.test_client()
    resp = client.delete("/users/999")
    data = json.loads(resp.data.decode())
    assert resp.status_code == 404
    assert "User 999 does not exist" in data["message"]


def test_update_user(test_app, test_database, add_user):
    test_database.session.query(User).delete()
    user = add_user("updateuser", "updateuser@seven.org")
    client = test_app.test_client()
    resp = client.put(
        f"/users/{user.id}",
        data=json.dumps({"username": "newname", "email": "newemail@seven.org"}),
        content_type="application/json",
    )
    data = json.loads(resp.data.decode())
    assert resp.status_code == 200
    assert data["message"] == f"{user.id} was updated!"
    updated_user = User.query.filter_by(id=user.id).first()
    assert updated_user.username == "newname"
    assert updated_user.email == "newemail@seven.org"


@pytest.mark.parametrize(
    "user_id, payload, status_code, message",
    [
        [1, {}, 400, "Input payload validation failed"],
        [1, {"email": "update@seven.org"}, 400, "Input payload validation failed"],
        [
            999,
            {"username": "updateuser", "email": "update@seven.org"},
            404,
            "User 999 does not exist",
        ],
    ],
)
def test_update_user_invalid(
    test_app, test_database, user_id, payload, status_code, message
):
    client = test_app.test_client()
    resp = client.put(
        f"/users/{user_id}", data=json.dumps(payload), content_type="application/json"
    )
    data = json.loads(resp.data.decode())
    assert resp.status_code == status_code
    assert message in data["message"]


def test_update_duplicate_email(test_app, test_database, add_user):
    test_database.session.query(User).delete()
    add_user("johndoe", "johndoe@seven.org")
    user = add_user("updateuser", "update@seven.org")
    client = test_app.test_client()
    resp = client.put(
        f"/users/{user.id}",
        data=json.dumps({"username": "updateuser", "email": "johndoe@seven.org"}),
        content_type="application/json",
    )
    data = json.loads(resp.data.decode())
    assert resp.status_code == 400
    assert "Sorry. That email already exists." in data["message"]

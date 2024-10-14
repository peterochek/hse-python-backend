from datetime import datetime
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from lecture_4.demo_service.api.main import create_app
from lecture_4.demo_service.api.utils import initialize
from lecture_4.demo_service.core.users import (
    UserInfo,
    UserRole,
    UserService,
    password_is_longer_than_8,
)


@pytest.fixture()
def test_client():
    app = create_app()
    user_service = UserService(password_validators=[password_is_longer_than_8])
    user_service.register(
        UserInfo(
            username="admin",
            name="admin",
            birthdate=datetime(2005, 1, 1),
            role=UserRole.ADMIN,
            password=SecretStr("123456789"),
        )
    )
    app.state.user_service = user_service
    return TestClient(app)


def register_user(client, **kwargs):
    return client.post("/user-register", json=kwargs)


@pytest.mark.parametrize(
    "username,name,birthdate,password,expected_status,expected_response",
    [
        (
            "test_user",
            "Joe",
            "2000-05-20",
            "123456789",
            HTTPStatus.OK,
            {
                "username": "test_user",
                "name": "Joe",
                "birthdate": "2000-05-20T00:00:00",
                "uid": 2,
                "role": "user",
            },
        ),
        (
            "test_user",
            "John",
            "2002-05-20",
            "1234567890",
            HTTPStatus.BAD_REQUEST,
            None,
        ),
        (
            "new_user",
            "Anna",
            "1999-07-15",
            "1234567",
            HTTPStatus.BAD_REQUEST,
            None,
        ),
    ],
)
def test_register_user(
    test_client, username, name, birthdate, password, expected_status, expected_response
):
    if expected_status == HTTPStatus.BAD_REQUEST and username == "test_user":
        register_user(
            test_client,
            username="test_user",
            name="Existing",
            birthdate="2000-01-01",
            password="123456789",
        )

    response = register_user(
        test_client,
        username=username,
        name=name,
        birthdate=birthdate,
        password=password,
    )
    assert response.status_code == expected_status
    if expected_response:
        assert response.json() == expected_response


@pytest.mark.parametrize(
    "params,auth,expected_status,expected_response",
    [
        (
            {"id": 2, "username": "test_user"},
            ("admin", "123456789"),
            HTTPStatus.BAD_REQUEST,
            None,
        ),
        ({}, ("admin", "123456789"), HTTPStatus.BAD_REQUEST, None),
        (
            {"id": 1},
            ("admin", "123456789"),
            HTTPStatus.OK,
            {
                "uid": 1,
                "username": "admin",
                "name": "admin",
                "birthdate": "2005-01-01T00:00:00",
                "role": "admin",
            },
        ),
        (
            {"username": "admin"},
            ("admin", "123456789"),
            HTTPStatus.OK,
            {
                "uid": 1,
                "username": "admin",
                "name": "admin",
                "birthdate": "2005-01-01T00:00:00",
                "role": "admin",
            },
        ),
        ({"id": 1}, ("admin", "wrongpass"), HTTPStatus.UNAUTHORIZED, None),
        (
            {"username": "nonexistent"},
            ("admin", "123456789"),
            HTTPStatus.NOT_FOUND,
            None,
        ),
    ],
)
def test_user_get(test_client, params, auth, expected_status, expected_response):
    response = test_client.post("/user-get", params=params, auth=auth)
    assert response.status_code == expected_status
    if expected_response:
        assert response.json() == expected_response


@pytest.mark.parametrize(
    "setup,params,auth,expected_status",
    [
        (None, {"id": 1}, ("admin", "123456789"), HTTPStatus.OK),
        (None, {"id": 10}, ("admin", "123456789"), HTTPStatus.BAD_REQUEST),
        (
            {
                "username": "test_user",
                "name": "Joe",
                "birthdate": "2000-05-20",
                "password": "123456789",
            },
            {"id": 1},
            ("test_user", "123456789"),
            HTTPStatus.FORBIDDEN,
        ),
    ],
)
def test_user_promote(test_client, setup, params, auth, expected_status):
    if setup:
        register_user(test_client, **setup)

    response = test_client.post("/user-promote", params=params, auth=auth)
    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_initialize():
    app = create_app()
    async with initialize(app):
        user_service = app.state.user_service
        admin = user_service.get_by_username("admin")
        assert admin.uid == 1
        admin_info = admin.info
        assert admin_info.username == "admin"
        assert admin_info.name == "admin"
        assert admin_info.birthdate == datetime.fromtimestamp(0.0)
        assert admin_info.role == UserRole.ADMIN
        assert admin_info.password == SecretStr("superSecretAdminPassword123")

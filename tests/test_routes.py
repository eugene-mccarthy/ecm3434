import pytest
from app import create_app
from config import TestingConfig


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.test_client() as client:
        yield client


def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_about_returns_200(client):
    response = client.get("/about")
    assert response.status_code == 200


def test_404_on_unknown_route(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404

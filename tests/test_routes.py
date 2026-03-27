import pytest
from app import create_app, db
from app.models import User, Category, Listing
from config import TestingConfig
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded_app(app):
    """App with minimal seed data for tests that need DB content."""
    with app.app_context():
        cat = Category(name="Heritage")
        db.session.add(cat)
        db.session.flush()

        user = User(
            username="tester",
            email="tester@example.com",
            password_hash=generate_password_hash("pass"),
        )
        db.session.add(user)
        db.session.flush()

        listing = Listing(
            title="Test Castle",
            description="A test listing.",
            category_id=cat.id,
            user_id=user.id,
            status="approved",
        )
        db.session.add(listing)
        db.session.commit()
    return app


# --- Public routes ---

def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_contains_brand(client):
    response = client.get("/")
    assert b"Community Tourist" in response.data


def test_404_on_unknown_route(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404


# --- Auth routes ---

def test_register_page_loads(client):
    response = client.get("/auth/register")
    assert response.status_code == 200


def test_login_page_loads(client):
    response = client.get("/auth/login")
    assert response.status_code == 200


def test_register_creates_user(client, app):
    response = client.post(
        "/auth/register",
        data={"username": "newuser", "email": "new@example.com", "password": "secret"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert User.query.filter_by(username="newuser").first() is not None


def test_register_duplicate_username(client, app):
    with app.app_context():
        db.session.add(User(
            username="taken",
            email="taken@example.com",
            password_hash=generate_password_hash("x"),
        ))
        db.session.commit()
    response = client.post(
        "/auth/register",
        data={"username": "taken", "email": "other@example.com", "password": "y"},
        follow_redirects=True,
    )
    assert b"already taken" in response.data


def test_login_invalid_credentials(client):
    response = client.post(
        "/auth/login",
        data={"email": "nobody@example.com", "password": "wrong"},
        follow_redirects=True,
    )
    assert b"Invalid" in response.data


# --- Listing routes ---

def test_listing_detail_returns_200(seeded_app):
    client = seeded_app.test_client()
    with seeded_app.app_context():
        listing = Listing.query.first()
    response = client.get(f"/listing/{listing.id}")
    assert response.status_code == 200
    assert b"Test Castle" in response.data


def test_listing_detail_404_for_missing(client):
    response = client.get("/listing/9999")
    assert response.status_code == 404


def test_add_listing_requires_login(client):
    response = client.get("/listing/add")
    assert response.status_code == 302
    assert b"/auth/login" in response.data


# --- Admin routes ---

def test_admin_panel_requires_login(client):
    response = client.get("/admin/")
    assert response.status_code == 302

"""
[TEST] Integration tests for key routes
Ticket: Write integration tests for key routes
Milestone: Sprint 1

Covers:
  - Unauthenticated POST to /listing/add → 302 redirect to /auth/login
  - Admin approve action → listing.status changes to 'approved'
  - Non-admin authenticated GET to /admin/ → 403 Forbidden
"""

import unittest
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Category, Listing, User
from config import TestingConfig


class TestIntegration(unittest.TestCase):

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self._seed()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _seed(self):
        cat = Category(name="Heritage")
        db.session.add(cat)
        db.session.flush()

        self.regular = User(
            username="visitor",
            email="visitor@example.com",
            password_hash=generate_password_hash("password"),
            is_admin=False,
        )
        self.admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=generate_password_hash("adminpass"),
            is_admin=True,
        )
        db.session.add_all([self.regular, self.admin])
        db.session.flush()

        self.pending_listing = Listing(
            title="Pending Place",
            description="Awaiting moderation.",
            category_id=cat.id,
            user_id=self.regular.id,
            status="pending",
        )
        db.session.add(self.pending_listing)
        db.session.commit()
        # Capture the ID before the session-bound object expires
        self.listing_id = self.pending_listing.id

    def _login(self, email, password):
        return self.client.post(
            "/auth/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )

    def _logout(self):
        self.client.get("/auth/logout", follow_redirects=True)

    # ------------------------------------------------------------------
    # Unauthenticated POST to /listing/add → 302 redirect to login
    # ------------------------------------------------------------------

    def test_unauthenticated_post_to_add_redirects_to_login(self):
        """
        An unauthenticated POST to /listing/add (the submission endpoint)
        must return 302 and redirect the client to /auth/login.
        """
        response = self.client.post(
            "/listing/add",
            data={"title": "Test", "description": "Desc", "category_id": 1},
        )
        self.assertEqual(
            response.status_code, 302,
            "Unauthenticated POST should redirect (302)",
        )
        location = response.headers.get("Location", "")
        self.assertIn(
            "/auth/login", location,
            f"Redirect location should point to /auth/login, got: {location}",
        )

    def test_unauthenticated_get_to_add_redirects_to_login(self):
        """GET /listing/add without a session also redirects to login."""
        response = self.client.get("/listing/add")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers.get("Location", ""))

    # ------------------------------------------------------------------
    # Admin approve action → listing status changes to 'approved'
    # ------------------------------------------------------------------

    def test_admin_approve_changes_status_to_approved(self):
        """
        When an admin POSTs to the approve endpoint the listing's status
        in the database must change from 'pending' to 'approved'.
        """
        self._login("admin@example.com", "adminpass")

        response = self.client.post(
            f"/admin/listing/{self.listing_id}/approve",
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        updated = Listing.query.get(self.listing_id)
        self.assertEqual(
            updated.status, "approved",
            "Listing status should be 'approved' after admin approval",
        )

    def test_admin_reject_changes_status_to_rejected(self):
        """Admin POST to reject endpoint sets listing status to 'rejected'."""
        self._login("admin@example.com", "adminpass")

        self.client.post(
            f"/admin/listing/{self.listing_id}/reject",
            follow_redirects=True,
        )

        updated = Listing.query.get(self.listing_id)
        self.assertEqual(updated.status, "rejected")

    def test_admin_panel_shows_pending_listings(self):
        """Admin GET to /admin/ renders the panel with the pending listing."""
        self._login("admin@example.com", "adminpass")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Pending Place", response.data)

    # ------------------------------------------------------------------
    # Non-admin GET to /admin → 403
    # ------------------------------------------------------------------

    def test_non_admin_get_admin_panel_returns_403(self):
        """
        An authenticated user without admin privileges must receive
        403 Forbidden when attempting to access /admin/.
        """
        self._login("visitor@example.com", "password")
        response = self.client.get("/admin/")
        self.assertEqual(
            response.status_code, 403,
            "A non-admin authenticated user should receive 403 on /admin/",
        )

    def test_non_admin_cannot_approve_listing(self):
        """A non-admin user POSTing to approve endpoint also receives 403."""
        self._login("visitor@example.com", "password")
        response = self.client.post(f"/admin/listing/{self.listing_id}/approve")
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_admin_panel_redirects_to_login(self):
        """Unauthenticated access to /admin/ redirects to login, not 403."""
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers.get("Location", ""))


if __name__ == "__main__":
    unittest.main()

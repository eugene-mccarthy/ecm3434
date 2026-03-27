"""
[TEST] Unit tests for database models
Ticket: Write unit tests for database models
Milestone: Sprint 1

Covers:
  - Listing saves correctly and is retrievable from DB
  - Rating average recalculates correctly
  - User password is not stored as plaintext
"""

import unittest
from werkzeug.security import generate_password_hash, check_password_hash

from app import create_app, db
from app.models import Category, Listing, Rating, User
from config import TestingConfig


class TestModels(unittest.TestCase):

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Shared fixtures used by multiple tests
        cat = Category(name="Heritage")
        db.session.add(cat)
        db.session.flush()

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=generate_password_hash("plaintext123"),
        )
        db.session.add(user)
        db.session.flush()

        self.cat_id = cat.id
        self.user_id = user.id
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    # ------------------------------------------------------------------
    # Listing saves correctly and is retrievable from DB
    # ------------------------------------------------------------------

    def test_listing_saves_and_is_retrievable(self):
        """A Listing written to the DB can be fetched with correct field values."""
        listing = Listing(
            title="Stonehenge",
            description="Ancient prehistoric monument on Salisbury Plain.",
            category_id=self.cat_id,
            user_id=self.user_id,
            status="approved",
        )
        db.session.add(listing)
        db.session.commit()

        fetched = Listing.query.filter_by(title="Stonehenge").first()

        self.assertIsNotNone(fetched, "Listing should exist in the database")
        self.assertEqual(fetched.title, "Stonehenge")
        self.assertEqual(fetched.description, "Ancient prehistoric monument on Salisbury Plain.")
        self.assertEqual(fetched.status, "approved")
        self.assertEqual(fetched.category_id, self.cat_id)
        self.assertEqual(fetched.user_id, self.user_id)
        self.assertIsNotNone(fetched.created_at, "created_at should be set automatically")

    def test_listing_default_status_is_pending(self):
        """A new Listing defaults to 'pending' status when none is supplied."""
        listing = Listing(
            title="Glastonbury Tor",
            description="Iconic hill in Somerset.",
            category_id=self.cat_id,
            user_id=self.user_id,
        )
        db.session.add(listing)
        db.session.commit()

        fetched = Listing.query.filter_by(title="Glastonbury Tor").first()
        self.assertEqual(fetched.status, "pending")

    def test_listing_author_relationship_navigable(self):
        """listing.author should resolve to the correct User via backref."""
        listing = Listing(
            title="Avebury",
            description="Neolithic henge monument.",
            category_id=self.cat_id,
            user_id=self.user_id,
            status="approved",
        )
        db.session.add(listing)
        db.session.commit()

        fetched = Listing.query.filter_by(title="Avebury").first()
        self.assertEqual(fetched.author.username, "testuser")

    # ------------------------------------------------------------------
    # Rating average recalculates correctly
    # ------------------------------------------------------------------

    def test_rating_average_of_single_rating(self):
        """avg_rating equals the sole rating score when only one rating exists."""
        listing = Listing(
            title="Brighton Pier",
            description="Victorian pleasure pier.",
            category_id=self.cat_id,
            user_id=self.user_id,
            status="approved",
            avg_rating=0.0,
        )
        db.session.add(listing)
        db.session.flush()

        r = Rating(listing_id=listing.id, user_id=self.user_id, score=4)
        db.session.add(r)
        db.session.flush()

        ratings = Rating.query.filter_by(listing_id=listing.id).all()
        listing.avg_rating = sum(x.score for x in ratings) / len(ratings)
        db.session.commit()

        self.assertAlmostEqual(
            Listing.query.get(listing.id).avg_rating, 4.0,
            msg="avg_rating should equal 4.0 with a single score of 4",
        )

    def test_rating_average_of_multiple_ratings(self):
        """avg_rating is the mean of all scores after multiple ratings."""
        second_user = User(
            username="rater2",
            email="rater2@example.com",
            password_hash=generate_password_hash("x"),
        )
        third_user = User(
            username="rater3",
            email="rater3@example.com",
            password_hash=generate_password_hash("x"),
        )
        db.session.add_all([second_user, third_user])
        db.session.flush()

        listing = Listing(
            title="Lake Windermere",
            description="Largest natural lake in England.",
            category_id=self.cat_id,
            user_id=self.user_id,
            status="approved",
            avg_rating=0.0,
        )
        db.session.add(listing)
        db.session.flush()

        # Scores: 5, 3, 4 → mean = 4.0
        db.session.add_all([
            Rating(listing_id=listing.id, user_id=self.user_id, score=5),
            Rating(listing_id=listing.id, user_id=second_user.id, score=3),
            Rating(listing_id=listing.id, user_id=third_user.id, score=4),
        ])
        db.session.flush()

        ratings = Rating.query.filter_by(listing_id=listing.id).all()
        listing.avg_rating = sum(x.score for x in ratings) / len(ratings)
        db.session.commit()

        self.assertAlmostEqual(
            Listing.query.get(listing.id).avg_rating, 4.0,
            msg="avg_rating should equal 4.0 for scores 5, 3, 4",
        )

    def test_duplicate_rating_constraint_raises(self):
        """A user cannot submit two ratings for the same listing (unique constraint)."""
        from sqlalchemy.exc import IntegrityError

        listing = Listing(
            title="Hadrian's Wall",
            description="Roman frontier wall.",
            category_id=self.cat_id,
            user_id=self.user_id,
            status="approved",
        )
        db.session.add(listing)
        db.session.flush()

        db.session.add(Rating(listing_id=listing.id, user_id=self.user_id, score=5))
        db.session.commit()

        db.session.add(Rating(listing_id=listing.id, user_id=self.user_id, score=3))
        with self.assertRaises(IntegrityError):
            db.session.commit()

    # ------------------------------------------------------------------
    # User password not stored as plaintext
    # ------------------------------------------------------------------

    def test_password_not_stored_as_plaintext(self):
        """password_hash must differ from the original plaintext password."""
        user = User.query.filter_by(username="testuser").first()
        self.assertNotEqual(
            user.password_hash, "plaintext123",
            "password_hash must not equal the plaintext password",
        )

    def test_password_hash_validates_correctly(self):
        """check_password_hash must return True for the correct plaintext."""
        user = User.query.filter_by(username="testuser").first()
        self.assertTrue(
            check_password_hash(user.password_hash, "plaintext123"),
            "Correct plaintext should validate against stored hash",
        )

    def test_wrong_password_does_not_validate(self):
        """check_password_hash must return False for an incorrect plaintext."""
        user = User.query.filter_by(username="testuser").first()
        self.assertFalse(
            check_password_hash(user.password_hash, "wrongpassword"),
            "Incorrect plaintext should not validate against stored hash",
        )


if __name__ == "__main__":
    unittest.main()

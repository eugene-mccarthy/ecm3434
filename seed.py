"""
seed.py — Populate the database with sample data for development.

Usage:
    python seed.py

Creates:
    - 5 categories
    - 2 users (regular + admin)
    - 10 approved listings across categories
    - Sample ratings
"""

from app import create_app, db
from app.models import User, Category, Listing, Rating
from werkzeug.security import generate_password_hash

app = create_app()

CATEGORIES = ["Heritage", "Beaches", "Nightlife", "Dining", "Activities"]

LISTINGS = [
    {
        "title": "Tintagel Castle",
        "description": (
            "Legendary birthplace of King Arthur, perched on a dramatic headland with "
            "stunning sea views. Explore centuries of history among the clifftop ruins."
        ),
        "category": "Heritage",
    },
    {
        "title": "Porthcurno Beach",
        "description": (
            "A stunning white-sand cove with crystal-clear turquoise water, sheltered by "
            "granite cliffs. One of Cornwall's most beautiful beaches and great for snorkelling."
        ),
        "category": "Beaches",
    },
    {
        "title": "Minack Theatre",
        "description": (
            "A unique open-air theatre carved into the clifftop, with breathtaking views "
            "over the Atlantic. Hosts plays and musicals throughout the summer season."
        ),
        "category": "Activities",
    },
    {
        "title": "The Salty Dog",
        "description": (
            "A lively seafront pub serving local Cornish ales and fresh seafood platters. "
            "Live music every Friday night with a fantastic harbour view from the terrace."
        ),
        "category": "Nightlife",
    },
    {
        "title": "Rick Stein's Seafood Restaurant",
        "description": (
            "World-renowned restaurant in Padstow serving the finest locally caught seafood "
            "in an elegant waterfront setting. Book well in advance."
        ),
        "category": "Dining",
    },
    {
        "title": "Eden Project",
        "description": (
            "Home to the world's largest indoor rainforest. Explore giant biomes packed with "
            "exotic plants from around the globe, set in a former china clay pit."
        ),
        "category": "Activities",
    },
    {
        "title": "Tate St Ives",
        "description": (
            "A striking gallery of modern and contemporary art with panoramic views over "
            "St Ives Bay. Free for under-18s and always thought-provoking."
        ),
        "category": "Heritage",
    },
    {
        "title": "Carbis Bay Beach",
        "description": (
            "A sheltered Blue Flag beach with golden sands, ideal for families. Calm waters "
            "make it perfect for swimming, paddleboarding and kayaking."
        ),
        "category": "Beaches",
    },
    {
        "title": "Falmouth Marina Bar",
        "description": (
            "A stylish waterfront cocktail bar with views over Falmouth harbour. Popular "
            "spot for sundowners and hosts local acoustic music nights at weekends."
        ),
        "category": "Nightlife",
    },
    {
        "title": "The Harbour Kitchen",
        "description": (
            "A cosy café serving authentic Cornish cream teas, homemade pasties and "
            "locally sourced lunches. The perfect reward after a bracing coastal walk."
        ),
        "category": "Dining",
    },
]

# Rating scores per listing (1–5)
SCORES = [5, 4, 5, 4, 5, 5, 4, 4, 3, 5]


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # --- Categories ---
        cats = {}
        for name in CATEGORIES:
            cat = Category(name=name)
            db.session.add(cat)
            cats[name] = cat
        db.session.flush()

        # --- Users ---
        regular = User(
            username="visitor1",
            email="visitor@example.com",
            password_hash=generate_password_hash("password123"),
            is_admin=False,
            points=0,
        )
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=generate_password_hash("adminpass"),
            is_admin=True,
            points=0,
        )
        db.session.add_all([regular, admin])
        db.session.flush()

        # --- Listings ---
        listings = []
        for data in LISTINGS:
            listing = Listing(
                title=data["title"],
                description=data["description"],
                category_id=cats[data["category"]].id,
                user_id=regular.id,
                status="approved",
                avg_rating=0.0,
            )
            db.session.add(listing)
            listings.append(listing)
        db.session.flush()

        # --- Ratings (admin rates all listings) ---
        for listing, score in zip(listings, SCORES):
            rating = Rating(
                listing_id=listing.id,
                user_id=admin.id,
                score=score,
            )
            db.session.add(rating)
            listing.avg_rating = float(score)

        db.session.commit()

        print("Database seeded successfully.")
        print(f"  Categories : {len(cats)}")
        print(f"  Users      : 2  (visitor1 / password123  |  admin / adminpass)")
        print(f"  Listings   : {len(listings)}")
        print(f"  Ratings    : {len(listings)}")


if __name__ == "__main__":
    seed()

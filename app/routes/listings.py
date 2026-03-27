import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Listing, Category, Rating

listings_bp = Blueprint("listings", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB


def _save_photo(file):
    """
    Validate and persist an uploaded photo.

    Returns the saved filename (str) or None if no file was provided.
    Raises ValueError with a user-friendly message on validation failure.
    """
    if not file or file.filename == "":
        return None

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Only JPG and PNG images are accepted.")

    # Measure size without loading the whole file into memory
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_UPLOAD_BYTES:
        raise ValueError("Photo must be 2 MB or smaller.")

    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    return filename


# ---------------------------------------------------------------------------

@listings_bp.route("/")
def index():
    category_id = request.args.get("category", type=int)
    query = Listing.query.filter_by(status="approved")
    if category_id:
        query = query.filter_by(category_id=category_id)
    listings = query.order_by(Listing.created_at.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template(
        "listings/index.html",
        title="Browse",
        listings=listings,
        categories=categories,
        selected_category=category_id,
    )


@listings_bp.route("/listing/<int:listing_id>")
def detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    user_rating = None
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(
            listing_id=listing_id, user_id=current_user.id
        ).first()
    return render_template(
        "listings/detail.html",
        title=listing.title,
        listing=listing,
        user_rating=user_rating,
    )


@listings_bp.route("/listing/add", methods=["GET", "POST"])
@login_required
def add():
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category_id = request.form.get("category_id", type=int)

        if not title or not description or not category_id:
            flash("Title, category, and description are all required.", "error")
            return render_template(
                "listings/add.html", title="Add Listing", categories=categories
            )

        try:
            photo_filename = _save_photo(request.files.get("photo"))
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template(
                "listings/add.html", title="Add Listing", categories=categories
            )

        listing = Listing(
            title=title,
            description=description,
            category_id=category_id,
            user_id=current_user.id,
            status="pending",
            photo_filename=photo_filename,
        )
        db.session.add(listing)
        current_user.points += 5
        db.session.commit()
        flash("Listing submitted for review. You earned 5 points!", "success")
        return redirect(url_for("listings.index"))

    return render_template("listings/add.html", title="Add Listing", categories=categories)


@listings_bp.route("/listing/<int:listing_id>/rate", methods=["POST"])
@login_required
def rate(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing.status != "approved":
        flash("Cannot rate this listing.", "error")
        return redirect(url_for("listings.detail", listing_id=listing_id))
    score = request.form.get("score", type=int)
    if not score or score < 1 or score > 5:
        flash("Score must be between 1 and 5.", "error")
        return redirect(url_for("listings.detail", listing_id=listing_id))
    existing = Rating.query.filter_by(
        listing_id=listing_id, user_id=current_user.id
    ).first()
    if existing:
        existing.score = score
    else:
        db.session.add(Rating(listing_id=listing_id, user_id=current_user.id, score=score))
        current_user.points += 1
    db.session.flush()
    all_ratings = Rating.query.filter_by(listing_id=listing_id).all()
    listing.avg_rating = sum(r.score for r in all_ratings) / len(all_ratings)
    db.session.commit()
    flash("Rating submitted!", "success")
    return redirect(url_for("listings.detail", listing_id=listing_id))

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import Listing

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Unauthenticated users are handled by @login_required (302 → login).
        # Authenticated non-admins get a hard 403.
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/")
@login_required
@admin_required
def panel():
    pending = Listing.query.filter_by(status="pending").order_by(Listing.created_at).all()
    return render_template("admin/panel.html", title="Admin Panel", pending=pending)


@admin_bp.route("/listing/<int:listing_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    listing.status = "approved"
    db.session.commit()
    flash(f'"{listing.title}" approved.', "success")
    return redirect(url_for("admin.panel"))


@admin_bp.route("/listing/<int:listing_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    listing.status = "rejected"
    db.session.commit()
    flash(f'"{listing.title}" rejected.', "info")
    return redirect(url_for("admin.panel"))

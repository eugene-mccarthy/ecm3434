from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from app.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("listings.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("auth/register.html", title="Register")
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return render_template("auth/register.html", title="Register")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("auth/register.html", title="Register")
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", title="Register")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("listings.index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("listings.index"))
        flash("Invalid email or password.", "error")
    return render_template("auth/login.html", title="Login")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("listings.index"))


@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("auth/profile.html", title="My Profile")

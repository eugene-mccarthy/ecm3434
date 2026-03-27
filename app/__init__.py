from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.listings import listings_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        _apply_migrations(db)

    return app


def _apply_migrations(db):
    """
    Lightweight schema migrations for SQLite.
    Adds any columns introduced after the initial db.create_all() so that
    existing databases are updated automatically on the next app start.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)

    # Guard: listings table may not exist yet in a brand-new test DB
    if "listings" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("listings")}

    pending = {
        "photo_filename": "ALTER TABLE listings ADD COLUMN photo_filename VARCHAR(256)",
    }

    for column, sql in pending.items():
        if column not in existing:
            db.session.execute(text(sql))
    db.session.commit()

import os

from flask import Flask

from . import db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-inventory-secret"),
        DATABASE=os.path.join(app.instance_path, "inventory.sqlite3"),
        ITEMS_PER_PAGE=10,
        SLOW_MOVING_DAYS=60,
        SLOW_MOVING_MAX_UNITS=5,
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    from .routes import bp

    app.register_blueprint(bp)

    with app.app_context():
        db.init_db()
        db.seed_db()

    return app

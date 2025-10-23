from flask import Flask
from .config import Settings
from .extensions.cache import cache
from .extensions.db import db
from .extensions.logger import configure_logging

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Settings())

    configure_logging(app)
    cache.init_app(app)
    db.init_app(app)

    from .blueprints.api import api_bp
    from .blueprints.web import web_bp
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(web_bp)

    with app.app_context():
        try:
            db.create_all()  # Dev only (SQLite). Use Alembic in prod.
        except Exception as e:
            app.logger.warning("DB init skipped: %s", e)

    return app

from pathlib import Path

from flask import Flask, send_from_directory

from .api import api


def create_app(test_config=None):
    """Application factory: mantém configuração, API e interface desacopladas."""
    frontend = Path(__file__).resolve().parent.parent / "frontend"
    app = Flask(__name__, static_folder=str(frontend), static_url_path="/static")
    app.config.from_mapping(JSON_SORT_KEYS=False)
    if test_config:
        app.config.update(test_config)
    app.register_blueprint(api, url_prefix="/api")

    @app.get("/")
    def index():
        return send_from_directory(frontend, "index.html")

    return app

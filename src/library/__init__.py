"""Library Management System - Flask application factory (models 5.1)."""
import os

import click
from flask import Flask

from library.clock import SystemClock
from library.db import Database
from library.rules import Rules


def create_app(config: dict | None = None) -> Flask:
    """Application Factory: builds the app and wires all layers together (dependency injection)."""
    app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
    app.config.update(
        DATABASE=os.environ.get("LIBRARY_DB", os.path.join(app.instance_path, "library.db")),
        SECRET_KEY=os.environ.get("LIBRARY_SECRET_KEY", "dev-only-change-me"),
        CLOCK=SystemClock(),
        RULES=Rules(),
    )
    if config:
        app.config.update(config)

    if app.config["DATABASE"] != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(app.config["DATABASE"])), exist_ok=True)
    db = Database(app.config["DATABASE"])
    db.init_schema()
    app.extensions["library_db"] = db

    @app.cli.command("init-db")
    def init_db_command():
        """Create the database tables (safe to run again)."""
        db.init_schema()
        click.echo(f"Database ready: {app.config['DATABASE']}")

    return app

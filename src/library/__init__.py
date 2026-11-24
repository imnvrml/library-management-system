"""Library Management System - Flask application factory (models 5.1)."""
import os

import click
from flask import Flask

from library.clock import SystemClock
from library.db import Database
from library.domain import Role
from library.errors import BusinessRuleError
from library.rules import Rules
from library.services import build_services


def create_app(config: dict | None = None) -> Flask:
    """Application Factory: builds the app and wires all layers together (dependency injection)."""
    app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
    app.config.update(
        DATABASE=os.environ.get("LIBRARY_DB", os.path.join(app.instance_path, "library.db")),
        SECRET_KEY=os.environ.get("LIBRARY_SECRET_KEY", "dev-only-change-me"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
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
    services = build_services(db, app.config["CLOCK"], app.config["RULES"])
    app.extensions["library"] = services

    from library.web import init_web
    init_web(app)

    @app.cli.command("init-db")
    def init_db_command():
        """Create the database tables (safe to run again)."""
        db.init_schema()
        click.echo(f"Database ready: {app.config['DATABASE']}")

    @app.cli.command("create-librarian")
    @click.option("--name", prompt="Full name")
    @click.option("--email", prompt="E-mail")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_librarian_command(name, email, password):
        """Create a librarian account (assumption A-03: the first librarian is created here)."""
        try:
            user = services.members.register(name, email, None, password, role=Role.LIBRARIAN)
        except BusinessRuleError as e:
            raise click.ClickException(e.message)
        click.echo(f"Librarian {user.email} created.")

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Fill an empty database with demo data for trying the system."""
        from library.demo import seed
        click.echo(seed(services))

    return app

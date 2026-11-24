"""Presentation layer (models 5.1, architecture): blueprints, access guard, CSRF check, error pages."""
import secrets
from functools import wraps

from flask import Flask, abort, current_app, flash, g, redirect, render_template, request, session, url_for

from library.domain import Role, azn
from library.errors import AccessDeniedError, BusinessRuleError


def services():
    return current_app.extensions["library"]


def role_required(*roles: Role):
    """Decorator pattern (FR-02, NFR-03): visitors go to the login page, wrong roles get HTTP 403."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if g.user is None:
                return redirect(url_for("auth.login", next=request.path))
            if g.user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        wrapper.allowed_roles = roles
        return wrapper
    return decorator


librarian_only = role_required(Role.LIBRARIAN)
member_only = role_required(Role.MEMBER)
any_user = role_required(Role.LIBRARIAN, Role.MEMBER)


def back(default_endpoint: str, **values):
    """Redirect to the page the form came from (same site only), else to a default page."""
    target = request.form.get("next") or ""
    if target.startswith("/") and not target.startswith("//"):
        return redirect(target)
    return redirect(url_for(default_endpoint, **values))


def parse_azn(text: str) -> int:
    """'0.40' -> 40 qəpik. Invalid input becomes 0, which the payment rule rejects."""
    try:
        whole, _, frac = (text or "").strip().replace(",", ".").partition(".")
        return int(whole or 0) * 100 + int((frac + "00")[:2] or 0)
    except ValueError:
        return 0


def init_web(app: Flask) -> None:
    from library.web import account, auth, catalogue, circulation, members, reservations

    for bp in (auth.bp, catalogue.bp, members.bp, circulation.bp, reservations.bp, account.bp):
        app.register_blueprint(bp)

    app.jinja_env.filters["azn"] = azn

    @app.before_request
    def load_user_and_check_csrf():
        g.user = None
        user_id = session.get("user_id")
        if user_id is not None:
            user = services().users.get(user_id)
            if user is None or not user.is_active:
                session.pop("user_id", None)   # deactivated accounts lose their session (FR-08)
            else:
                g.user = user
        if request.method == "POST" and request.form.get("csrf_token") != session.get("csrf"):
            abort(400, "Missing or wrong form token. Reload the page and try again.")

    @app.context_processor
    def template_helpers():
        def csrf_token():
            if "csrf" not in session:
                session["csrf"] = secrets.token_hex(16)
            return session["csrf"]
        return {"csrf_token": csrf_token, "Role": Role, "today": services().clock.today()}

    @app.errorhandler(AccessDeniedError)
    def access_denied(_error):
        return render_template("error.html", code=403, message="You may not open this page."), 403

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, message="You may not open this page."), 403

    @app.errorhandler(400)
    def bad_request(error):
        return render_template("error.html", code=400, message=error.description), 400

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.route("/")
    def home():
        if g.user is None:
            return redirect(url_for("auth.login"))
        return redirect(url_for("circulation.dashboard" if g.user.role == Role.LIBRARIAN else "account.my_account"))


def flash_error(error: BusinessRuleError) -> None:
    flash(error.message, "error")

"""auth_bp (UC-01, FR-01)."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from library.errors import BusinessRuleError
from library.web import services

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            user = services().auth.login(request.form.get("email", ""), request.form.get("password", ""))
        except BusinessRuleError as e:
            return render_template("login.html", error=e.message, email=request.form.get("email", "")), 200
        csrf = session.get("csrf")
        session.clear()                     # new session on login
        session["user_id"], session["csrf"] = user.id, csrf
        target = request.args.get("next") or ""
        if target.startswith("/") and not target.startswith("//"):
            return redirect(target)
        return redirect(url_for("home"))
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    flash("You are logged out.", "info")
    return redirect(url_for("auth.login"))

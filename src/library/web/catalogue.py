"""catalogue_bp (UC-02, UC-03; FR-03 to FR-06)."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from library.domain import Role
from library.errors import BusinessRuleError
from library.web import any_user, flash_error, librarian_only, services

bp = Blueprint("catalogue", __name__)


@bp.route("/titles")
@any_user
def search():
    q = request.args.get("q", "")
    return render_template("titles.html", q=q, results=services().catalogue.search(q))


@bp.route("/titles", methods=["POST"])
@librarian_only
def add_title():
    f = request.form
    try:
        title = services().catalogue.add_title(f.get("isbn"), f.get("title"), f.get("author"), f.get("publisher"),
                                               f.get("year"))
    except BusinessRuleError as e:
        flash_error(e)
        return redirect(url_for("catalogue.search"))
    flash(f"Added “{title.title}”.", "success")
    return redirect(url_for("catalogue.title", title_id=title.id))


@bp.route("/titles/<int:title_id>")
@any_user
def title(title_id):
    s = services()
    t = s.titles.get(title_id)
    if t is None:
        abort(404)
    copies = s.copies.of_title(title_id)
    holders = {}
    if g.user.role == Role.LIBRARIAN:
        for c in copies:
            member_id = s.queue.holder_of(c)
            if member_id:
                holders[c.id] = s.users.get(member_id).full_name
    queue_length = len(s.reservations.waiting_queue(title_id))
    return render_template("title.html", t=t, copies=copies, holders=holders, queue_length=queue_length,
                           available=s.copies.count_available(title_id))


@bp.route("/titles/<int:title_id>/copies", methods=["POST"])
@librarian_only
def add_copy(title_id):
    try:
        copy = services().catalogue.add_copy(title_id, request.form.get("code", ""))
        note = " It is on hold for the first member in the queue." if copy.status == "on_hold" else ""
        flash(f"Copy {copy.code} added.{note}", "success")
    except BusinessRuleError as e:
        flash_error(e)
    return redirect(url_for("catalogue.title", title_id=title_id))


@bp.route("/copies/<int:copy_id>/withdraw", methods=["POST"])
@librarian_only
def withdraw_copy(copy_id):
    s = services()
    copy = s.copies.get(copy_id)
    try:
        s.catalogue.withdraw_copy(copy_id)
        flash(f"Copy {copy.code} withdrawn.", "success")
    except BusinessRuleError as e:
        flash_error(e)
    return redirect(url_for("catalogue.title", title_id=copy.title_id) if copy else url_for("catalogue.search"))

"""members_bp (UC-04, UC-11; FR-07, FR-08, FR-18)."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from library.domain import Role, azn
from library.errors import BusinessRuleError
from library.web import flash_error, librarian_only, parse_azn, services

bp = Blueprint("members", __name__)


@bp.route("/members")
@librarian_only
def index():
    s = services()
    rows = [(m, len(s.loans.open_loans_of(m.id)), s.members.balance(m.id)) for m in s.users.members()]
    return render_template("members.html", rows=rows)


@bp.route("/members", methods=["POST"])
@librarian_only
def register():
    f = request.form
    try:
        member = services().members.register(f.get("full_name"), f.get("email"), f.get("phone"), f.get("password"))
    except BusinessRuleError as e:
        flash_error(e)
        return redirect(url_for("members.index"))
    flash(f"Member {member.full_name} registered.", "success")
    return redirect(url_for("members.detail", member_id=member.id))


@bp.route("/members/<int:member_id>")
@librarian_only
def detail(member_id):
    s = services()
    member = s.users.get(member_id)
    if member is None or member.role != Role.MEMBER:
        abort(404)
    loans = [(loan, s.copies.get(loan.copy_id), s.titles.get(s.copies.get(loan.copy_id).title_id))
             for loan in s.loans.history_of(member_id)]
    return render_template("member.html", m=member, loans=loans, balance=s.members.balance(member_id),
                           reservations=s.queue.active_of(member_id))


@bp.route("/members/<int:member_id>/payments", methods=["POST"])
@librarian_only
def record_payment(member_id):
    s = services()
    try:
        s.members.record_payment(member_id, parse_azn(request.form.get("amount", "")), g.user.id)
        flash(f"Payment recorded. New balance {azn(s.members.balance(member_id))}.", "success")
    except BusinessRuleError as e:
        flash_error(e)
    return redirect(url_for("members.detail", member_id=member_id))


@bp.route("/members/<int:member_id>/deactivate", methods=["POST"])
@librarian_only
def deactivate(member_id):
    try:
        services().members.deactivate(member_id)
        flash("Member deactivated.", "success")
    except BusinessRuleError as e:
        flash_error(e)
    return redirect(url_for("members.detail", member_id=member_id) if services().users.get(member_id)
                    else url_for("members.index"))

"""circulation_bp (UC-05, UC-06, UC-07, UC-12; FR-09 to FR-12, FR-15, FR-19)."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from library.domain import CopyStatus, Role, azn
from library.errors import BusinessRuleError
from library.web import any_user, back, flash_error, librarian_only, services

bp = Blueprint("circulation", __name__)


@bp.route("/dashboard")
@librarian_only
def dashboard():
    s = services()
    expired = s.queue.expire_holds()          # A-05: holds are also processed when the dashboard opens
    return render_template("dashboard.html", stats=s.circulation.desk_stats(), overdue=len(s.circulation.overdue_loans()),
                           expired=expired)


@bp.route("/circulation/checkout", methods=["POST"])
@librarian_only
def checkout():
    s = services()
    member = s.users.find_by_email(request.form.get("member_email", ""))
    try:
        if member is None or member.role != Role.MEMBER:
            raise BusinessRuleError("Member not found")
        loan = s.circulation.checkout(member.id, request.form.get("copy_code", ""))
        flash(f"Checked out {request.form['copy_code'].strip()} to {member.full_name}, due {loan.due_date}.",
              "success")
    except BusinessRuleError as e:
        flash_error(e)
    return back("circulation.dashboard")


@bp.route("/circulation/return", methods=["POST"])
@librarian_only
def return_copy():
    s = services()
    code = request.form.get("copy_code", "").strip()
    try:
        loan = s.circulation.return_copy(code)
        message = f"Returned {code}. Fine {azn(loan.fine_qepik)}."
        if s.copies.find_by_code(code).status == CopyStatus.ON_HOLD:
            message += " The copy is on hold for the next member in the queue — put it on the hold shelf."
        flash(message, "success")
    except BusinessRuleError as e:
        flash_error(e)
    return back("circulation.dashboard")


@bp.route("/loans/<int:loan_id>/renew", methods=["POST"])
@any_user
def renew(loan_id):
    try:
        loan = services().circulation.renew(loan_id, g.user)   # AccessDeniedError -> 403
        flash(f"Renewed. New due date {loan.due_date}.", "success")
    except BusinessRuleError as e:
        flash_error(e)
    if g.user.role == Role.MEMBER:
        return redirect(url_for("account.my_account"))
    return back("circulation.dashboard")


@bp.route("/circulation/overdue")
@librarian_only
def overdue():
    return render_template("overdue.html", rows=services().circulation.overdue_loans())

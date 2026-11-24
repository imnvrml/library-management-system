"""reservations_bp (UC-08, UC-09; FR-13, FR-16)."""
from flask import Blueprint, flash, g, redirect, request, url_for

from library.domain import Role
from library.errors import BusinessRuleError
from library.web import any_user, flash_error, services

bp = Blueprint("reservations", __name__)


@bp.route("/titles/<int:title_id>/reserve", methods=["POST"])
@any_user
def place(title_id):
    s = services()
    try:
        if g.user.role == Role.LIBRARIAN:      # on behalf of a member (FR-13)
            member = s.users.find_by_email(request.form.get("member_email", ""))
            if member is None or member.role != Role.MEMBER:
                raise BusinessRuleError("Member not found")
        else:
            member = g.user
        reservation = s.queue.place(member.id, title_id)
        flash(f"Reserved. Your position in the queue: {s.queue.position(reservation)}.", "success")
    except BusinessRuleError as e:
        flash_error(e)
    return redirect(url_for("catalogue.title", title_id=title_id))


@bp.route("/reservations/<int:reservation_id>/cancel", methods=["POST"])
@any_user
def cancel(reservation_id):
    try:
        services().queue.cancel(reservation_id, g.user)       # AccessDeniedError -> 403
        flash("Reservation cancelled.", "success")
    except BusinessRuleError as e:
        flash_error(e)
    if g.user.role == Role.MEMBER:
        return redirect(url_for("account.my_account"))
    return redirect(request.referrer or url_for("circulation.dashboard"))

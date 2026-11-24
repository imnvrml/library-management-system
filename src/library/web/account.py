"""account_bp (UC-10, FR-17): the member's own loans, balance and reservations."""
from flask import Blueprint, g, render_template

from library.web import member_only, services

bp = Blueprint("account", __name__)


@bp.route("/account")
@member_only
def my_account():
    s = services()
    loans = []
    for loan in s.loans.history_of(g.user.id):
        copy = s.copies.get(loan.copy_id)
        loans.append((loan, copy, s.titles.get(copy.title_id)))
    return render_template("account.html", loans=loans, balance=s.members.balance(g.user.id),
                           reservations=s.queue.active_of(g.user.id))

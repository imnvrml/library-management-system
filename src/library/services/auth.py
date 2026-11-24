"""AuthService (FR-01, NFR-02)."""
from werkzeug.security import check_password_hash, generate_password_hash

from library.domain import User
from library.errors import BusinessRuleError
from library.repositories import UserRepository

# Werkzeug's default is a salted scrypt hash. Tests lower the cost (tests/conftest.py) to keep the suite fast.
HASH_METHOD = "scrypt"


class AuthService:
    def __init__(self, users: UserRepository):
        self.users = users

    def login(self, email: str, password: str) -> User:
        user = self.users.find_by_email(email or "")
        # one message for unknown e-mail and wrong password, so the form does not reveal which e-mails exist
        if user is None or not check_password_hash(user.password_hash, password or ""):
            raise BusinessRuleError("Invalid e-mail or password")
        if not user.is_active:
            raise BusinessRuleError("Account is deactivated")
        return user

    @staticmethod
    def hash_password(plain: str) -> str:
        return generate_password_hash(plain, method=HASH_METHOD)

"""Exceptions raised by the service layer; the web layer turns them into messages or HTTP 403."""


class BusinessRuleError(Exception):
    """A business rule refused the action. The message is shown to the user as is."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AccessDeniedError(Exception):
    """The user may not act on this record (FR-02 AC3). Shown as HTTP 403."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message)
        self.message = message

class DomainError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, details: list | None = None):
        self.code, self.message, self.status = code, message, status
        self.details = details or []

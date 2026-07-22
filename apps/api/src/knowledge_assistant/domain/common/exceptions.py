class DomainError(Exception):
    """Base class for all domain exceptions."""


class ValidationError(DomainError):
    """Raised when input validation fails."""


class ConflictError(DomainError):
    """Raised when a resource already exists."""


class NotFoundError(DomainError):
    """Raised when a resource cannot be found."""


class AuthenticationError(DomainError):
    """Raised when authentication fails."""


class AuthorizationError(DomainError):
    """Raised when authorization fails."""


class RateLimitError(AuthenticationError):
    """Raised when a security or usage limit is exceeded."""


class BusinessRuleViolation(DomainError):
    """Raised when a business rule is violated."""
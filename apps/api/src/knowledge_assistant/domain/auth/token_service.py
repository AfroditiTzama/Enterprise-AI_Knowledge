from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any


class TokenService(ABC):

    @abstractmethod
    def create_token(
        self,
        subject: str,
        expires_delta: timedelta,
        additional_claims: dict[str, Any] | None = None,
    ) -> str:
        ...

    @abstractmethod
    def verify_token(
        self,
        token: str,
    ) -> dict[str, Any]:
        ...
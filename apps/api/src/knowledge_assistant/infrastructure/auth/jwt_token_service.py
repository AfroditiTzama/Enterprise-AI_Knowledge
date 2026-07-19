from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from knowledge_assistant.core.config import get_settings
from knowledge_assistant.domain.auth.token_service import TokenService


class JWTTokenService(TokenService):

    def __init__(self) -> None:
        settings = get_settings()

        self._secret = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm

    def create_token(
        self,
        subject: str,
        expires_delta: timedelta,
        additional_claims: dict[str, Any] | None = None,
    ) -> str:

        now = datetime.now(UTC)

        payload = {
            "sub": subject,
            "iat": now,
            "exp": now + expires_delta,
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(
            payload,
            self._secret,
            algorithm=self._algorithm,
        )

    def verify_token(
        self,
        token: str,
    ) -> dict[str, Any]:

        return jwt.decode(
            token,
            self._secret,
            algorithms=[self._algorithm],
        )
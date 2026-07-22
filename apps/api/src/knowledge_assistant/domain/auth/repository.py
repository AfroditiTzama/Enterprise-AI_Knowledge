from abc import ABC, abstractmethod
from uuid import UUID

from knowledge_assistant.domain.auth.entities import (
    AccountActionToken,
    AuthSession,
    LoginSecurityState,
    SecurityEvent,
)


class AuthRepository(ABC):
    @abstractmethod
    async def add_session(self, session: AuthSession) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_session(self, session_id: UUID) -> AuthSession | None:
        raise NotImplementedError

    @abstractmethod
    async def update_session(self, session: AuthSession) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_active_sessions(self, user_id: UUID) -> list[AuthSession]:
        raise NotImplementedError

    @abstractmethod
    async def revoke_session(self, session_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke_all_sessions(
        self,
        user_id: UUID,
        *,
        except_session_id: UUID | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_action_token(self, token: AccountActionToken) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_action_token(
        self,
        *,
        token_hash: str,
        purpose: str,
    ) -> AccountActionToken | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_action_token_used(self, token_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def invalidate_action_tokens(
        self,
        *,
        user_id: UUID,
        purpose: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_security_event(self, event: SecurityEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_security_events(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
    ) -> list[SecurityEvent]:
        raise NotImplementedError

    @abstractmethod
    async def get_login_security_state(
        self,
        key_hash: str,
    ) -> LoginSecurityState | None:
        raise NotImplementedError

    @abstractmethod
    async def upsert_login_security_state(
        self,
        state: LoginSecurityState,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear_login_security_state(self, key_hash: str) -> None:
        raise NotImplementedError

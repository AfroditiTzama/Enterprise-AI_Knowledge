from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_assistant.domain.auth.entities import (
    AccountActionToken,
    AuthSession,
    LoginSecurityState,
    SecurityEvent,
)
from knowledge_assistant.domain.auth.repository import AuthRepository
from knowledge_assistant.infrastructure.database.models.auth import (
    AccountActionTokenModel,
    AuthSessionModel,
    LoginSecurityStateModel,
    SecurityEventModel,
)


class SQLAlchemyAuthRepository(AuthRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_session(self, session: AuthSession) -> None:
        self._session.add(
            AuthSessionModel(
                id=session.id,
                user_id=session.user_id,
                refresh_token_hash=session.refresh_token_hash,
                csrf_token_hash=session.csrf_token_hash,
                expires_at=session.expires_at,
                created_at=session.created_at,
                last_used_at=session.last_used_at,
                user_agent=session.user_agent,
                ip_address=session.ip_address,
                revoked_at=session.revoked_at,
            )
        )
        await self._session.flush()

    async def get_session(self, session_id: UUID) -> AuthSession | None:
        model = await self._session.get(AuthSessionModel, session_id)
        if model is None:
            return None
        return self._session_to_domain(model)

    async def update_session(self, session: AuthSession) -> None:
        model = await self._session.get(AuthSessionModel, session.id)
        if model is None:
            raise ValueError(f"Session not found: {session.id}")
        model.refresh_token_hash = session.refresh_token_hash
        model.csrf_token_hash = session.csrf_token_hash
        model.expires_at = session.expires_at
        model.last_used_at = session.last_used_at
        model.user_agent = session.user_agent
        model.ip_address = session.ip_address
        model.revoked_at = session.revoked_at
        await self._session.flush()

    async def list_active_sessions(self, user_id: UUID) -> list[AuthSession]:
        now = datetime.now(UTC)
        statement = (
            select(AuthSessionModel)
            .where(
                AuthSessionModel.user_id == user_id,
                AuthSessionModel.revoked_at.is_(None),
                AuthSessionModel.expires_at > now,
            )
            .order_by(AuthSessionModel.last_used_at.desc())
        )
        result = await self._session.execute(statement)
        return [
            self._session_to_domain(model)
            for model in result.scalars().all()
        ]

    async def revoke_session(self, session_id: UUID) -> None:
        now = datetime.now(UTC)
        await self._session.execute(
            update(AuthSessionModel)
            .where(
                AuthSessionModel.id == session_id,
                AuthSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await self._session.flush()

    async def revoke_all_sessions(
        self,
        user_id: UUID,
        *,
        except_session_id: UUID | None = None,
    ) -> None:
        now = datetime.now(UTC)
        statement = update(AuthSessionModel).where(
            AuthSessionModel.user_id == user_id,
            AuthSessionModel.revoked_at.is_(None),
        )
        if except_session_id is not None:
            statement = statement.where(
                AuthSessionModel.id != except_session_id
            )
        await self._session.execute(statement.values(revoked_at=now))
        await self._session.flush()

    async def add_action_token(self, token: AccountActionToken) -> None:
        self._session.add(
            AccountActionTokenModel(
                id=token.id,
                user_id=token.user_id,
                purpose=token.purpose,
                token_hash=token.token_hash,
                expires_at=token.expires_at,
                created_at=token.created_at,
                used_at=token.used_at,
            )
        )
        await self._session.flush()

    async def get_active_action_token(
        self,
        *,
        token_hash: str,
        purpose: str,
    ) -> AccountActionToken | None:
        now = datetime.now(UTC)
        statement = select(AccountActionTokenModel).where(
            AccountActionTokenModel.token_hash == token_hash,
            AccountActionTokenModel.purpose == purpose,
            AccountActionTokenModel.used_at.is_(None),
            AccountActionTokenModel.expires_at > now,
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return AccountActionToken(
            id=model.id,
            user_id=model.user_id,
            purpose=model.purpose,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            created_at=model.created_at,
            used_at=model.used_at,
        )

    async def mark_action_token_used(self, token_id: UUID) -> None:
        await self._session.execute(
            update(AccountActionTokenModel)
            .where(AccountActionTokenModel.id == token_id)
            .values(used_at=datetime.now(UTC))
        )
        await self._session.flush()

    async def invalidate_action_tokens(
        self,
        *,
        user_id: UUID,
        purpose: str,
    ) -> None:
        await self._session.execute(
            update(AccountActionTokenModel)
            .where(
                AccountActionTokenModel.user_id == user_id,
                AccountActionTokenModel.purpose == purpose,
                AccountActionTokenModel.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
        )
        await self._session.flush()

    async def add_security_event(self, event: SecurityEvent) -> None:
        self._session.add(
            SecurityEventModel(
                id=event.id,
                user_id=event.user_id,
                event_type=event.event_type,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                metadata_json=event.metadata_json,
                created_at=event.created_at,
            )
        )
        await self._session.flush()

    async def list_security_events(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
    ) -> list[SecurityEvent]:
        statement = (
            select(SecurityEventModel)
            .where(SecurityEventModel.user_id == user_id)
            .order_by(SecurityEventModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(statement)
        return [
            SecurityEvent(
                id=model.id,
                user_id=model.user_id,
                event_type=model.event_type,
                ip_address=model.ip_address,
                user_agent=model.user_agent,
                metadata_json=model.metadata_json,
                created_at=model.created_at,
            )
            for model in result.scalars().all()
        ]

    async def get_login_security_state(
        self,
        key_hash: str,
    ) -> LoginSecurityState | None:
        model = await self._session.get(LoginSecurityStateModel, key_hash)
        if model is None:
            return None
        return LoginSecurityState(
            key_hash=model.key_hash,
            failed_attempts=model.failed_attempts,
            first_failed_at=model.first_failed_at,
            locked_until=model.locked_until,
            updated_at=model.updated_at,
        )

    async def upsert_login_security_state(
        self,
        state: LoginSecurityState,
    ) -> None:
        model = await self._session.get(
            LoginSecurityStateModel,
            state.key_hash,
        )
        if model is None:
            self._session.add(
                LoginSecurityStateModel(
                    key_hash=state.key_hash,
                    failed_attempts=state.failed_attempts,
                    first_failed_at=state.first_failed_at,
                    locked_until=state.locked_until,
                    updated_at=state.updated_at,
                )
            )
        else:
            model.failed_attempts = state.failed_attempts
            model.first_failed_at = state.first_failed_at
            model.locked_until = state.locked_until
            model.updated_at = state.updated_at
        await self._session.flush()

    async def clear_login_security_state(self, key_hash: str) -> None:
        await self._session.execute(
            delete(LoginSecurityStateModel).where(
                LoginSecurityStateModel.key_hash == key_hash
            )
        )
        await self._session.flush()

    @staticmethod
    def _session_to_domain(model: AuthSessionModel) -> AuthSession:
        return AuthSession(
            id=model.id,
            user_id=model.user_id,
            refresh_token_hash=model.refresh_token_hash,
            csrf_token_hash=model.csrf_token_hash,
            expires_at=model.expires_at,
            created_at=model.created_at,
            last_used_at=model.last_used_at,
            user_agent=model.user_agent,
            ip_address=model.ip_address,
            revoked_at=model.revoked_at,
        )

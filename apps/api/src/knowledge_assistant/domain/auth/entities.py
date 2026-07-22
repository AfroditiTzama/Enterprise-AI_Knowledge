from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID


@dataclass(slots=True)
class AuthSession:
    id: UUID
    user_id: UUID
    refresh_token_hash: str
    csrf_token_hash: str
    expires_at: datetime
    created_at: datetime
    last_used_at: datetime
    user_agent: str
    ip_address: str
    revoked_at: datetime | None = None

    def is_active(self, now: datetime | None = None) -> bool:
        reference = now or datetime.now(UTC)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return self.revoked_at is None and expires_at > reference


@dataclass(slots=True)
class AccountActionToken:
    id: UUID
    user_id: UUID
    purpose: str
    token_hash: str
    expires_at: datetime
    created_at: datetime
    used_at: datetime | None = None

    def is_active(self, now: datetime | None = None) -> bool:
        reference = now or datetime.now(UTC)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return self.used_at is None and expires_at > reference


@dataclass(slots=True)
class SecurityEvent:
    id: UUID
    user_id: UUID | None
    event_type: str
    ip_address: str
    user_agent: str
    metadata_json: str
    created_at: datetime


@dataclass(slots=True)
class LoginSecurityState:
    key_hash: str
    failed_attempts: int
    first_failed_at: datetime | None
    locked_until: datetime | None
    updated_at: datetime

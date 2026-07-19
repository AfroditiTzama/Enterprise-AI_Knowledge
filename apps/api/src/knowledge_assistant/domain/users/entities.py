from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from knowledge_assistant.domain.common.exceptions import BusinessRuleViolation
from knowledge_assistant.domain.common.value_objects.email import Email


@dataclass(slots=True)
class User:
    id: UUID
    email: Email
    hashed_password: str
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    def verify_email(self, now: datetime) -> None:
        if self.is_verified:
            raise BusinessRuleViolation("User email is already verified.")

        self.is_verified = True
        self.updated_at = now

    def deactivate(self, now: datetime) -> None:
        if not self.is_active:
            raise BusinessRuleViolation("User is already inactive.")

        self.is_active = False
        self.updated_at = now

    def activate(self, now: datetime) -> None:
        if self.is_active:
            raise BusinessRuleViolation("User is already active.")

        self.is_active = True
        self.updated_at = now

    def change_password(
        self,
        hashed_password: str,
        now: datetime,
    ) -> None:
        if not hashed_password.strip():
            raise BusinessRuleViolation("Hashed password cannot be empty.")

        self.hashed_password = hashed_password
        self.updated_at = now
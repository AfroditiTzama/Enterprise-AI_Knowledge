from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from knowledge_assistant.domain.common.exceptions import BusinessRuleViolation
from knowledge_assistant.domain.common.value_objects.email import Email


_ALLOWED_THEMES = {"system", "light", "dark"}
_ALLOWED_BEHAVIORS = {"concise", "balanced", "detailed"}
_ALLOWED_LANGUAGES = {"en", "el"}


@dataclass(slots=True)
class User:
    id: UUID
    email: Email
    hashed_password: str
    full_name: str
    is_active: bool
    is_verified: bool
    auth_version: int
    preferred_language: str
    theme_preference: str
    assistant_behavior: str
    created_at: datetime
    updated_at: datetime
    email_verified_at: datetime | None = None

    def verify_email(self, now: datetime) -> None:
        if self.is_verified:
            raise BusinessRuleViolation("User email is already verified.")

        self.is_verified = True
        self.email_verified_at = now
        self.updated_at = now

    def deactivate(self, now: datetime) -> None:
        if not self.is_active:
            raise BusinessRuleViolation("User is already inactive.")

        self.is_active = False
        self.auth_version += 1
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
        self.auth_version += 1
        self.updated_at = now

    def update_profile(
        self,
        *,
        full_name: str,
        preferred_language: str,
        theme_preference: str,
        assistant_behavior: str,
        now: datetime,
    ) -> None:
        normalized_name = full_name.strip()
        if len(normalized_name) < 2:
            raise BusinessRuleViolation(
                "Full name must contain at least 2 characters."
            )

        language = preferred_language.strip().lower()
        if language not in _ALLOWED_LANGUAGES:
            raise BusinessRuleViolation(
                "Preferred language must be English or Greek."
            )

        theme = theme_preference.strip().lower()
        if theme not in _ALLOWED_THEMES:
            raise BusinessRuleViolation(
                "Theme preference must be system, light or dark."
            )

        behavior = assistant_behavior.strip().lower()
        if behavior not in _ALLOWED_BEHAVIORS:
            raise BusinessRuleViolation(
                "Assistant behavior must be concise, balanced or detailed."
            )

        self.full_name = normalized_name
        self.preferred_language = language
        self.theme_preference = theme
        self.assistant_behavior = behavior
        self.updated_at = now

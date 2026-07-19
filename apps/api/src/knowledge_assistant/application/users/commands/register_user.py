from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from knowledge_assistant.domain.common.exceptions import (
    ConflictError,
    ValidationError,
)
from knowledge_assistant.domain.common.value_objects.email import Email
from knowledge_assistant.domain.security.password_hasher import PasswordHasher
from knowledge_assistant.domain.users.entities import User
from knowledge_assistant.domain.users.repository import UserRepository


@dataclass(slots=True, frozen=True)
class RegisterUserCommand:
    email: str
    password: str
    full_name: str


class RegisterUserUseCase:

    def __init__(
        self,
        repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:

        self._repository = repository
        self._password_hasher = password_hasher

    async def execute(
        self,
        command: RegisterUserCommand,
    ) -> User:

        email = Email(command.email)

        full_name = command.full_name.strip()

        if len(full_name) < 2:
            raise ValidationError(
                "Full name must contain at least 2 characters."
            )

        if len(command.password) < 8:
            raise ValidationError(
                "Password must contain at least 8 characters."
            )

        if await self._repository.exists_by_email(email):
            raise ConflictError(
                "Email is already registered."
            )

        now = datetime.now(UTC)

        user = User(
            id=uuid4(),
            email=email,
            hashed_password=self._password_hasher.hash(
                command.password
            ),
            full_name=full_name,
            is_active=True,
            is_verified=False,
            created_at=now,
            updated_at=now,
        )

        await self._repository.add(user)

        return user
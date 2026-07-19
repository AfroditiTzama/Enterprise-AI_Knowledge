from dataclasses import dataclass
from datetime import timedelta

from knowledge_assistant.domain.auth.token_service import TokenService
from knowledge_assistant.domain.common.exceptions import AuthenticationError
from knowledge_assistant.domain.common.value_objects.email import Email
from knowledge_assistant.domain.security.password_hasher import PasswordHasher
from knowledge_assistant.domain.users.repository import UserRepository


@dataclass(slots=True, frozen=True)
class LoginUserCommand:
    email: str
    password: str


@dataclass(slots=True, frozen=True)
class LoginResult:
    access_token: str
    token_type: str
    expires_in: int


class LoginUserUseCase:
    def __init__(
        self,
        repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._repository = repository
        self._password_hasher = password_hasher
        self._token_service = token_service

    async def execute(
        self,
        command: LoginUserCommand,
    ) -> LoginResult:
        email = Email(command.email)

        user = await self._repository.get_by_email(email)

        if user is None:
            raise AuthenticationError("Invalid email or password.")

        password_is_valid = self._password_hasher.verify(
            user.hashed_password,
            command.password,
        )

        if not password_is_valid:
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationError("Your account is inactive.")

        expires_in = 15 * 60

        access_token = self._token_service.create_token(
            subject=str(user.id),
            expires_delta=timedelta(seconds=expires_in),
            additional_claims={
                "type": "access",
            },
        )

        return LoginResult(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        )
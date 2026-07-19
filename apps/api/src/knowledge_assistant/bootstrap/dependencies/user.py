from fastapi import Depends

from knowledge_assistant.application.users.commands.login_user import (
    LoginUserUseCase,
)
from knowledge_assistant.application.users.commands.register_user import (
    RegisterUserUseCase,
)
from knowledge_assistant.bootstrap.dependencies.database import DatabaseSession
from knowledge_assistant.domain.auth.token_service import TokenService
from knowledge_assistant.domain.security.password_hasher import PasswordHasher
from knowledge_assistant.infrastructure.auth.jwt_token_service import (
    JWTTokenService,
)
from knowledge_assistant.infrastructure.database.repositories.user_repository import (
    SQLAlchemyUserRepository,
)
from knowledge_assistant.infrastructure.security.argon2_password_hasher import (
    Argon2PasswordHasher,
)
from typing import Annotated
from uuid import UUID

import jwt
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from knowledge_assistant.domain.common.exceptions import (
    AuthenticationError,
    AuthorizationError,
)
from knowledge_assistant.domain.users.entities import User


def get_user_repository(
    session: DatabaseSession,
) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(session)


def get_password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()


def get_token_service() -> TokenService:
    return JWTTokenService()

bearer_scheme = HTTPBearer(
    auto_error=False,
)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    repository: SQLAlchemyUserRepository = Depends(
        get_user_repository,
    ),
    token_service: TokenService = Depends(
        get_token_service,
    ),
) -> User:

    if credentials is None:
        raise AuthenticationError(
            "Authentication credentials were not provided."
        )

    if credentials.scheme.lower() != "bearer":
        raise AuthenticationError(
            "Invalid authentication scheme."
        )

    try:
        payload = token_service.verify_token(
            credentials.credentials,
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError(
            "Your access token has expired."
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError(
            "Invalid access token."
        ) from exc

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject:
        raise AuthenticationError(
            "The access token does not contain a valid subject."
        )

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise AuthenticationError(
            "The access token contains an invalid user identifier."
        ) from exc

    user = await repository.get_by_id(user_id)

    if user is None:
        raise AuthenticationError(
            "The user associated with this token no longer exists."
        )

    if not user.is_active:
        raise AuthorizationError(
            "Your account is inactive."
        )

    return user


CurrentUserDependency = Annotated[
    User,
    Depends(get_current_user),
]

def get_register_user_use_case(
    repository: SQLAlchemyUserRepository = Depends(
        get_user_repository,
    ),
    password_hasher: PasswordHasher = Depends(
        get_password_hasher,
    ),
) -> RegisterUserUseCase:

    return RegisterUserUseCase(
        repository=repository,
        password_hasher=password_hasher,
    )


def get_login_user_use_case(
    repository: SQLAlchemyUserRepository = Depends(
        get_user_repository,
    ),
    password_hasher: PasswordHasher = Depends(
        get_password_hasher,
    ),
    token_service: TokenService = Depends(
        get_token_service,
    ),
) -> LoginUserUseCase:

    return LoginUserUseCase(
        repository=repository,
        password_hasher=password_hasher,
        token_service=token_service,
    )
from typing import Annotated

from fastapi import APIRouter, Depends, status

from knowledge_assistant.application.users.commands.login_user import (
    LoginUserCommand,
    LoginUserUseCase,
)
from knowledge_assistant.application.users.commands.register_user import (
    RegisterUserCommand,
    RegisterUserUseCase,
)
from knowledge_assistant.bootstrap.dependencies.user import (
    CurrentUserDependency,
    get_login_user_use_case,
    get_register_user_use_case,
)
from knowledge_assistant.presentation.api.v1.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


RegisterUserDependency = Annotated[
    RegisterUserUseCase,
    Depends(get_register_user_use_case),
]


LoginUserDependency = Annotated[
    LoginUserUseCase,
    Depends(get_login_user_use_case),
]


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    payload: RegisterRequest,
    use_case: RegisterUserDependency,
) -> RegisterResponse:

    user = await use_case.execute(
        RegisterUserCommand(
            email=str(payload.email),
            password=payload.password,
            full_name=payload.full_name,
        )
    )

    return RegisterResponse(
        id=user.id,
        email=str(user.email),
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login user",
)
async def login(
    payload: LoginRequest,
    use_case: LoginUserDependency,
) -> LoginResponse:

    result = await use_case.execute(
        LoginUserCommand(
            email=str(payload.email),
            password=payload.password,
        )
    )

    return LoginResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user",
)
async def get_me(
    current_user: CurrentUserDependency,
) -> CurrentUserResponse:

    return CurrentUserResponse(
        id=current_user.id,
        email=str(current_user.email),
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
    )
from uuid import UUID

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_assistant.domain.common.value_objects.email import Email
from knowledge_assistant.domain.users.entities import User
from knowledge_assistant.domain.users.repository import UserRepository
from knowledge_assistant.infrastructure.database.mappers.user_mapper import (
    UserMapper,
)
from knowledge_assistant.infrastructure.database.models.user import UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        statement = select(UserModel).where(
            UserModel.id == user_id,
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        return None if model is None else UserMapper.to_domain(model)

    async def get_by_email(
        self,
        email: Email,
    ) -> User | None:
        statement = select(UserModel).where(
            UserModel.email == str(email),
        )
        result = await self._session.execute(statement)
        model = result.scalar_one_or_none()
        return None if model is None else UserMapper.to_domain(model)

    async def exists_by_email(
        self,
        email: Email,
    ) -> bool:
        statement = select(
            exists().where(UserModel.email == str(email))
        )
        result = await self._session.execute(statement)
        return bool(result.scalar())

    async def add(
        self,
        user: User,
    ) -> None:
        model = UserMapper.to_model(user)
        self._session.add(model)
        await self._session.flush()

    async def update(
        self,
        user: User,
    ) -> None:
        model = await self._session.get(UserModel, user.id)
        if model is None:
            raise ValueError(f"User not found: {user.id}")

        model.email = str(user.email)
        model.hashed_password = user.hashed_password
        model.full_name = user.full_name
        model.is_active = user.is_active
        model.is_verified = user.is_verified
        model.auth_version = user.auth_version
        model.preferred_language = user.preferred_language
        model.theme_preference = user.theme_preference
        model.assistant_behavior = user.assistant_behavior
        model.email_verified_at = user.email_verified_at
        model.updated_at = user.updated_at
        await self._session.flush()

    async def delete(
        self,
        user_id: UUID,
    ) -> None:
        await self._session.execute(
            delete(UserModel).where(UserModel.id == user_id)
        )
        await self._session.flush()

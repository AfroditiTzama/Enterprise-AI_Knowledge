from uuid import UUID

from sqlalchemy import exists, select
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

        if model is None:
            return None

        return UserMapper.to_domain(model)

    async def get_by_email(
        self,
        email: Email,
    ) -> User | None:

        statement = select(UserModel).where(
            UserModel.email == str(email),
        )

        result = await self._session.execute(statement)

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return UserMapper.to_domain(model)

    async def exists_by_email(
        self,
        email: Email,
    ) -> bool:

        statement = select(
            exists().where(
                UserModel.email == str(email),
            )
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
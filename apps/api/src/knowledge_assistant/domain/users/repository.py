from abc import ABC, abstractmethod
from uuid import UUID

from knowledge_assistant.domain.common.value_objects.email import Email
from knowledge_assistant.domain.users.entities import User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(
        self,
        email: Email,
    ) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def exists_by_email(
        self,
        email: Email,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def add(
        self,
        user: User,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        user: User,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(
        self,
        user_id: UUID,
    ) -> None:
        raise NotImplementedError

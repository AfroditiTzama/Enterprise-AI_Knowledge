from abc import ABC, abstractmethod
from uuid import UUID

from knowledge_assistant.domain.users.entities import User
from knowledge_assistant.domain.common.value_objects.email import Email


class UserRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        ...

    @abstractmethod
    async def get_by_email(
        self,
        email: Email,
    ) -> User | None:
        ...

    @abstractmethod
    async def exists_by_email(
        self,
        email: Email,
    ) -> bool:
        ...

    @abstractmethod
    async def add(
        self,
        user: User,
    ) -> None:
        ...
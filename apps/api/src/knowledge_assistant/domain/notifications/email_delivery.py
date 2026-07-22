from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EmailMessage:
    recipient: str
    subject: str
    text_body: str


class EmailDelivery(ABC):
    @abstractmethod
    async def send(self, message: EmailMessage) -> None:
        raise NotImplementedError

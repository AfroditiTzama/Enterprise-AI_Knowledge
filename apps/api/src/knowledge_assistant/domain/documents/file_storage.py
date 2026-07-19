from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class StoredFile:
    stored_filename: str
    storage_path: str
    size_bytes: int


class FileStorage(ABC):
    @abstractmethod
    async def save(
        self,
        *,
        file_content: bytes,
        original_filename: str,
    ) -> StoredFile:
        """Store a file and return its storage metadata."""
        raise NotImplementedError

    @abstractmethod
    async def read(self, storage_path: str) -> bytes:
        """Read and return the contents of a stored file."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        """Delete a previously stored file."""
        raise NotImplementedError
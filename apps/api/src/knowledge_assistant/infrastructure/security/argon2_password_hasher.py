from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError

from knowledge_assistant.domain.security.password_hasher import (
    PasswordHasher,
)


class Argon2PasswordHasher(PasswordHasher):

    def __init__(self) -> None:
        self._hasher = Argon2Hasher()

    def hash(
        self,
        password: str,
    ) -> str:

        return self._hasher.hash(password)

    def verify(
        self,
        hashed_password: str,
        password: str,
    ) -> bool:

        try:
            return self._hasher.verify(
                hashed_password,
                password,
            )

        except VerifyMismatchError:
            return False
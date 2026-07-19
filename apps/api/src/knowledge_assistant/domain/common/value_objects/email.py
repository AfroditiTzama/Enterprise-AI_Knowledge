from dataclasses import dataclass

from pydantic import EmailStr, TypeAdapter

from knowledge_assistant.domain.common.exceptions import ValidationError

_email_adapter = TypeAdapter(EmailStr)


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        try:
            normalized = _email_adapter.validate_python(self.value)
        except Exception as exc:
            raise ValidationError("Invalid email address.") from exc

        object.__setattr__(
            self,
            "value",
            normalized.lower(),
        )

    def __str__(self) -> str:
        return self.value
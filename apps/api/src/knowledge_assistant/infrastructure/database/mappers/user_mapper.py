from knowledge_assistant.domain.common.value_objects.email import Email
from knowledge_assistant.domain.users.entities import User
from knowledge_assistant.infrastructure.database.models.user import UserModel


class UserMapper:
    @staticmethod
    def to_domain(
        model: UserModel,
    ) -> User:
        return User(
            id=model.id,
            email=Email(model.email),
            hashed_password=model.hashed_password,
            full_name=model.full_name,
            is_active=model.is_active,
            is_verified=model.is_verified,
            auth_version=model.auth_version,
            preferred_language=model.preferred_language,
            theme_preference=model.theme_preference,
            assistant_behavior=model.assistant_behavior,
            email_verified_at=model.email_verified_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: User,
    ) -> UserModel:
        return UserModel(
            id=entity.id,
            email=str(entity.email),
            hashed_password=entity.hashed_password,
            full_name=entity.full_name,
            is_active=entity.is_active,
            is_verified=entity.is_verified,
            auth_version=entity.auth_version,
            preferred_language=entity.preferred_language,
            theme_preference=entity.theme_preference,
            assistant_behavior=entity.assistant_behavior,
            email_verified_at=entity.email_verified_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

"""secure auth sessions and profile preferences

Revision ID: d4e8f1a2b3c4
Revises: c9d8e7f6a5b4
Create Date: 2026-07-22 13:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "d4e8f1a2b3c4"
down_revision: str | None = "c9d8e7f6a5b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "auth_version",
                sa.Integer(),
                nullable=False,
                server_default="1",
            )
        )
        batch_op.add_column(
            sa.Column(
                "preferred_language",
                sa.String(length=16),
                nullable=False,
                server_default="en",
            )
        )
        batch_op.add_column(
            sa.Column(
                "theme_preference",
                sa.String(length=16),
                nullable=False,
                server_default="system",
            )
        )
        batch_op.add_column(
            sa.Column(
                "assistant_behavior",
                sa.String(length=32),
                nullable=False,
                server_default="balanced",
            )
        )
        batch_op.add_column(
            sa.Column(
                "email_verified_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=64), nullable=False),
        sa.Column("csrf_token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.String(length=500), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_auth_sessions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_auth_sessions"),
    )
    op.create_index(
        "ix_auth_sessions_user_id",
        "auth_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_auth_sessions_expires_at",
        "auth_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_auth_sessions_revoked_at",
        "auth_sessions",
        ["revoked_at"],
        unique=False,
    )

    op.create_table(
        "account_action_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(length=64), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_account_action_tokens_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_account_action_tokens"),
        sa.UniqueConstraint(
            "token_hash",
            name="uq_account_action_tokens_token_hash",
        ),
    )
    op.create_index(
        "ix_account_action_tokens_user_id",
        "account_action_tokens",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_account_action_tokens_purpose",
        "account_action_tokens",
        ["purpose"],
        unique=False,
    )
    op.create_index(
        "ix_account_action_tokens_token_hash",
        "account_action_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_account_action_tokens_expires_at",
        "account_action_tokens",
        ["expires_at"],
        unique=False,
    )

    op.create_table(
        "security_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("user_agent", sa.String(length=500), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_security_events_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_security_events"),
    )
    op.create_index(
        "ix_security_events_user_id",
        "security_events",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_security_events_event_type",
        "security_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_security_events_created_at",
        "security_events",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "login_security_states",
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("failed_attempts", sa.Integer(), nullable=False),
        sa.Column("first_failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint(
            "key_hash",
            name="pk_login_security_states",
        ),
    )
    op.create_index(
        "ix_login_security_states_locked_until",
        "login_security_states",
        ["locked_until"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_login_security_states_locked_until",
        table_name="login_security_states",
    )
    op.drop_table("login_security_states")

    op.drop_index("ix_security_events_created_at", table_name="security_events")
    op.drop_index("ix_security_events_event_type", table_name="security_events")
    op.drop_index("ix_security_events_user_id", table_name="security_events")
    op.drop_table("security_events")

    op.drop_index(
        "ix_account_action_tokens_expires_at",
        table_name="account_action_tokens",
    )
    op.drop_index(
        "ix_account_action_tokens_token_hash",
        table_name="account_action_tokens",
    )
    op.drop_index(
        "ix_account_action_tokens_purpose",
        table_name="account_action_tokens",
    )
    op.drop_index(
        "ix_account_action_tokens_user_id",
        table_name="account_action_tokens",
    )
    op.drop_table("account_action_tokens")

    op.drop_index("ix_auth_sessions_revoked_at", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_expires_at", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("email_verified_at")
        batch_op.drop_column("assistant_behavior")
        batch_op.drop_column("theme_preference")
        batch_op.drop_column("preferred_language")
        batch_op.drop_column("auth_version")

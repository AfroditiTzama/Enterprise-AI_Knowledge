"""create documents table

Revision ID: c77fa0bd1b98
Revises: 6d742e35c230
Create Date: 2026-07-17 15:14:59.495554
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c77fa0bd1b98"
down_revision: Union[str, Sequence[str], None] = "6d742e35c230"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column(
            "original_filename",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "stored_filename",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "storage_path",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "content_type",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "size_bytes",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "UPLOADED",
                "PROCESSING",
                "PROCESSED",
                "FAILED",
                name="document_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_documents_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_documents"),
        ),
        sa.UniqueConstraint(
            "storage_path",
            name=op.f("uq_documents_storage_path"),
        ),
        sa.UniqueConstraint(
            "stored_filename",
            name=op.f("uq_documents_stored_filename"),
        ),
    )

    op.create_index(
        op.f("ix_documents_owner_id"),
        "documents",
        ["owner_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_documents_owner_id"),
        table_name="documents",
    )

    op.drop_table("documents")
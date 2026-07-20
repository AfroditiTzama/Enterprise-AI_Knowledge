"""make wiki page document optional

Revision ID: 8c41b7e29a6d
Revises: 4d2e7f1a9b3c
Create Date: 2026-07-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "8c41b7e29a6d"
down_revision: str | None = "4d2e7f1a9b3c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


NAMING_CONVENTION = {
    "fk": (
        "fk_%(table_name)s_%(column_0_name)s_"
        "%(referred_table_name)s"
    ),
}


def upgrade() -> None:
    with op.batch_alter_table(
        "wiki_pages",
        recreate="always",
        naming_convention=NAMING_CONVENTION,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_wiki_pages_document_id_documents",
            type_="foreignkey",
        )

        batch_op.alter_column(
            "document_id",
            existing_type=sa.Uuid(),
            existing_nullable=False,
            nullable=True,
        )

        batch_op.create_foreign_key(
            "fk_wiki_pages_document_id_documents",
            "documents",
            ["document_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table(
        "wiki_pages",
        recreate="always",
        naming_convention=NAMING_CONVENTION,
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_wiki_pages_document_id_documents",
            type_="foreignkey",
        )

        batch_op.alter_column(
            "document_id",
            existing_type=sa.Uuid(),
            existing_nullable=True,
            nullable=False,
        )

        batch_op.create_foreign_key(
            "fk_wiki_pages_document_id_documents",
            "documents",
            ["document_id"],
            ["id"],
            ondelete="CASCADE",
        )

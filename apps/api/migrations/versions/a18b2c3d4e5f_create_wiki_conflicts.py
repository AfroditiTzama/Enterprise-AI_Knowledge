"""create wiki conflicts

Revision ID: a18b2c3d4e5f
Revises: 8c41b7e29a6d
Create Date: 2026-07-22
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a18b2c3d4e5f"
down_revision: str | None = "8c41b7e29a6d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wiki_page_conflicts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("wiki_page_id", sa.Uuid(), nullable=False),
        sa.Column("source_document_id", sa.Uuid(), nullable=True),
        sa.Column("existing_statement", sa.Text(), nullable=False),
        sa.Column("incoming_statement", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("resolution_note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["wiki_page_id"],
            ["wiki_pages.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_document_id"],
            ["documents.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_wiki_page_conflicts_owner_id"),
        "wiki_page_conflicts",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_wiki_page_conflicts_wiki_page_id"),
        "wiki_page_conflicts",
        ["wiki_page_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_wiki_page_conflicts_source_document_id"),
        "wiki_page_conflicts",
        ["source_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_wiki_page_conflicts_status"),
        "wiki_page_conflicts",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_wiki_page_conflicts_status"),
        table_name="wiki_page_conflicts",
    )
    op.drop_index(
        op.f("ix_wiki_page_conflicts_source_document_id"),
        table_name="wiki_page_conflicts",
    )
    op.drop_index(
        op.f("ix_wiki_page_conflicts_wiki_page_id"),
        table_name="wiki_page_conflicts",
    )
    op.drop_index(
        op.f("ix_wiki_page_conflicts_owner_id"),
        table_name="wiki_page_conflicts",
    )
    op.drop_table("wiki_page_conflicts")

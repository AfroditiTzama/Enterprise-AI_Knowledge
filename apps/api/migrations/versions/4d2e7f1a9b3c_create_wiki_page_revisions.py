"""create wiki page revisions

Revision ID: 4d2e7f1a9b3c
Revises: 79e67fa88d9d
Create Date: 2026-07-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "4d2e7f1a9b3c"
down_revision: str | None = "79e67fa88d9d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wiki_page_revisions",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "wiki_page_id",
            sa.Uuid(),
            nullable=True,
        ),
        sa.Column(
            "owner_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "page_slug",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "revision_number",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "summary",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "content_markdown",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "operation",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "triggering_document_id",
            sa.Uuid(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["wiki_page_id"],
            ["wiki_pages.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["triggering_document_id"],
            ["documents.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_id",
            "page_slug",
            "revision_number",
            name=(
                "uq_wiki_page_revisions_"
                "owner_slug_revision"
            ),
        ),
    )

    op.create_index(
        "ix_wiki_page_revisions_wiki_page_id",
        "wiki_page_revisions",
        ["wiki_page_id"],
        unique=False,
    )

    op.create_index(
        "ix_wiki_page_revisions_owner_id",
        "wiki_page_revisions",
        ["owner_id"],
        unique=False,
    )

    op.create_index(
        "ix_wiki_page_revisions_page_slug",
        "wiki_page_revisions",
        ["page_slug"],
        unique=False,
    )

    op.create_index(
        "ix_wiki_page_revisions_triggering_document_id",
        "wiki_page_revisions",
        ["triggering_document_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_wiki_page_revisions_triggering_document_id",
        table_name="wiki_page_revisions",
    )

    op.drop_index(
        "ix_wiki_page_revisions_page_slug",
        table_name="wiki_page_revisions",
    )

    op.drop_index(
        "ix_wiki_page_revisions_owner_id",
        table_name="wiki_page_revisions",
    )

    op.drop_index(
        "ix_wiki_page_revisions_wiki_page_id",
        table_name="wiki_page_revisions",
    )

    op.drop_table("wiki_page_revisions")

"""create wiki tables

Revision ID: 79e67fa88d9d
Revises: 0826fea916a6
Create Date: 2026-07-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "79e67fa88d9d"
down_revision: str | None = "0826fea916a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wiki_pages",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "owner_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "slug",
            sa.String(length=255),
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
            ["document_id"],
            ["documents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_id",
            "slug",
            name="uq_wiki_pages_owner_slug",
        ),
    )

    op.create_index(
        "ix_wiki_pages_owner_id",
        "wiki_pages",
        ["owner_id"],
        unique=False,
    )

    op.create_index(
        "ix_wiki_pages_document_id",
        "wiki_pages",
        ["document_id"],
        unique=False,
    )

    op.create_index(
        "ix_wiki_pages_slug",
        "wiki_pages",
        ["slug"],
        unique=False,
    )

    op.create_table(
        "wiki_page_sources",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "wiki_page_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "chunk_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "page_number",
            sa.Integer(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["document_chunks.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["wiki_page_id"],
            ["wiki_pages.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "wiki_page_id",
            "chunk_id",
            name="uq_wiki_page_sources_page_chunk",
        ),
    )

    op.create_index(
        "ix_wiki_page_sources_wiki_page_id",
        "wiki_page_sources",
        ["wiki_page_id"],
        unique=False,
    )

    op.create_index(
        "ix_wiki_page_sources_chunk_id",
        "wiki_page_sources",
        ["chunk_id"],
        unique=False,
    )

    op.create_table(
        "wiki_page_links",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "source_page_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "target_page_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "label",
            sa.String(length=255),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_page_id"],
            ["wiki_pages.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_page_id"],
            ["wiki_pages.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_page_id",
            "target_page_id",
            "label",
            name="uq_wiki_page_links_source_target_label",
        ),
    )

    op.create_index(
        "ix_wiki_page_links_source_page_id",
        "wiki_page_links",
        ["source_page_id"],
        unique=False,
    )

    op.create_index(
        "ix_wiki_page_links_target_page_id",
        "wiki_page_links",
        ["target_page_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_wiki_page_links_target_page_id",
        table_name="wiki_page_links",
    )

    op.drop_index(
        "ix_wiki_page_links_source_page_id",
        table_name="wiki_page_links",
    )

    op.drop_table("wiki_page_links")

    op.drop_index(
        "ix_wiki_page_sources_chunk_id",
        table_name="wiki_page_sources",
    )

    op.drop_index(
        "ix_wiki_page_sources_wiki_page_id",
        table_name="wiki_page_sources",
    )

    op.drop_table("wiki_page_sources")

    op.drop_index(
        "ix_wiki_pages_slug",
        table_name="wiki_pages",
    )

    op.drop_index(
        "ix_wiki_pages_document_id",
        table_name="wiki_pages",
    )

    op.drop_index(
        "ix_wiki_pages_owner_id",
        table_name="wiki_pages",
    )

    op.drop_table("wiki_pages")
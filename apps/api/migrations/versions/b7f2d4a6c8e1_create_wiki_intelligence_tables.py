"""create wiki intelligence tables

Revision ID: b7f2d4a6c8e1
Revises: a18b2c3d4e5f
Create Date: 2026-07-22
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b7f2d4a6c8e1"
down_revision: str | None = "a18b2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wiki_claim_citations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("wiki_page_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=False),
        sa.Column("claim_key", sa.String(length=255), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
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
            ["chunk_id"],
            ["document_chunks.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "wiki_page_id",
            "claim_key",
            "chunk_id",
            name="uq_wiki_claim_citations_page_key_chunk",
        ),
    )
    op.create_index(
        op.f("ix_wiki_claim_citations_owner_id"),
        "wiki_claim_citations",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_wiki_claim_citations_wiki_page_id"),
        "wiki_claim_citations",
        ["wiki_page_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_wiki_claim_citations_chunk_id"),
        "wiki_claim_citations",
        ["chunk_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_wiki_claim_citations_claim_key"),
        "wiki_claim_citations",
        ["claim_key"],
        unique=False,
    )

    op.create_table(
        "wiki_maintenance_suggestions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("issue_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("page_ids_json", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_id",
            "fingerprint",
            name="uq_wiki_maintenance_owner_fingerprint",
        ),
    )
    op.create_index(
        op.f("ix_wiki_maintenance_suggestions_owner_id"),
        "wiki_maintenance_suggestions",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_wiki_maintenance_suggestions_issue_type"),
        "wiki_maintenance_suggestions",
        ["issue_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_wiki_maintenance_suggestions_status"),
        "wiki_maintenance_suggestions",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_wiki_maintenance_suggestions_status"),
        table_name="wiki_maintenance_suggestions",
    )
    op.drop_index(
        op.f("ix_wiki_maintenance_suggestions_issue_type"),
        table_name="wiki_maintenance_suggestions",
    )
    op.drop_index(
        op.f("ix_wiki_maintenance_suggestions_owner_id"),
        table_name="wiki_maintenance_suggestions",
    )
    op.drop_table("wiki_maintenance_suggestions")

    op.drop_index(
        op.f("ix_wiki_claim_citations_claim_key"),
        table_name="wiki_claim_citations",
    )
    op.drop_index(
        op.f("ix_wiki_claim_citations_chunk_id"),
        table_name="wiki_claim_citations",
    )
    op.drop_index(
        op.f("ix_wiki_claim_citations_wiki_page_id"),
        table_name="wiki_claim_citations",
    )
    op.drop_index(
        op.f("ix_wiki_claim_citations_owner_id"),
        table_name="wiki_claim_citations",
    )
    op.drop_table("wiki_claim_citations")

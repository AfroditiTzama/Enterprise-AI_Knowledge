"""document intelligence metadata and llm usage

Revision ID: e5f6a7b8c9d0
Revises: d4e8f1a2b3c4
Create Date: 2026-07-22 14:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e8f1a2b3c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("document_chunks") as batch_op:
        batch_op.add_column(
            sa.Column("section_title", sa.String(length=500), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "section_path_json",
                sa.Text(),
                nullable=False,
                server_default="[]",
            )
        )
        batch_op.add_column(
            sa.Column(
                "content_type",
                sa.String(length=32),
                nullable=False,
                server_default="text",
            )
        )
        batch_op.add_column(
            sa.Column("parent_text", sa.Text(), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "extraction_method",
                sa.String(length=32),
                nullable=False,
                server_default="native",
            )
        )
        batch_op.create_index(
            "ix_document_chunks_section_title",
            ["section_title"],
            unique=False,
        )
        batch_op.create_index(
            "ix_document_chunks_content_type",
            ["content_type"],
            unique=False,
        )

    op.create_table(
        "llm_usage_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name="fk_llm_usage_events_owner_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_llm_usage_events"),
    )
    op.create_index(
        "ix_llm_usage_events_owner_id",
        "llm_usage_events",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        "ix_llm_usage_events_created_at",
        "llm_usage_events",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_llm_usage_events_created_at",
        table_name="llm_usage_events",
    )
    op.drop_index(
        "ix_llm_usage_events_owner_id",
        table_name="llm_usage_events",
    )
    op.drop_table("llm_usage_events")

    with op.batch_alter_table("document_chunks") as batch_op:
        batch_op.drop_index("ix_document_chunks_content_type")
        batch_op.drop_index("ix_document_chunks_section_title")
        batch_op.drop_column("extraction_method")
        batch_op.drop_column("parent_text")
        batch_op.drop_column("content_type")
        batch_op.drop_column("section_path_json")
        batch_op.drop_column("section_title")

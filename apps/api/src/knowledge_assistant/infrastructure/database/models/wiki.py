from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from knowledge_assistant.infrastructure.database.base import Base


class WikiPageModel(Base):
    __tablename__ = "wiki_pages"
    __table_args__ = (
        UniqueConstraint(
            "owner_id",
            "slug",
            name="uq_wiki_pages_owner_slug",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    owner_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    content_markdown: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class WikiPageSourceModel(Base):
    __tablename__ = "wiki_page_sources"
    __table_args__ = (
        UniqueConstraint(
            "wiki_page_id",
            "chunk_id",
            name="uq_wiki_page_sources_page_chunk",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    wiki_page_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "wiki_pages.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    chunk_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "document_chunks.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    page_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )


class WikiPageLinkModel(Base):
    __tablename__ = "wiki_page_links"
    __table_args__ = (
        UniqueConstraint(
            "source_page_id",
            "target_page_id",
            "label",
            name="uq_wiki_page_links_source_target_label",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    source_page_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "wiki_pages.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    target_page_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "wiki_pages.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    label: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="related",
    )
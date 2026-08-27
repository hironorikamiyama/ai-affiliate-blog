from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.article_tag import article_tags


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    blog_id: Mapped[int] = mapped_column(
        ForeignKey(
            "blogs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    affiliate_program_id: Mapped[int] = mapped_column(
        ForeignKey("affiliate_programs.id"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        unique=True,
        index=True,
    )

    keyword: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    meta_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"),
        nullable=True,
        index=True,
    )

    blog = relationship(
        "Blog",
        back_populates="articles",
    )

    affiliate_program = relationship(
        "AffiliateProgram",
        back_populates="articles",
    )

    images = relationship(
        "ArticleImage",
        back_populates="article",
        cascade="all, delete-orphan",
        order_by="ArticleImage.position",
    )

    category = relationship(
        "Category",
        back_populates="articles",
    )

    tags = relationship(
        "Tag",
        secondary=article_tags,
        back_populates="articles",
    )
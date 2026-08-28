from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.database import Base
from app.models.article_tag import article_tags


class Tag(Base):
    __tablename__ = "tags"

    __table_args__ = (
        UniqueConstraint(
            "blog_id",
            "name",
            name="uq_tags_blog_id_name",
        ),
        UniqueConstraint(
            "blog_id",
            "slug",
            name="uq_tags_blog_id_slug",
        ),
    )

    id: Mapped[int] = mapped_column(
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

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
    )

    blog = relationship(
        "Blog",
        back_populates="tags",
    )

    articles = relationship(
        "Article",
        secondary=article_tags,
        back_populates="tags",
    )
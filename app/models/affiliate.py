from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AffiliateProgram(Base):
    __tablename__ = "affiliate_programs"

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

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    asp_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    affiliate_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    reward_amount: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reward_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="fixed",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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

    blog = relationship(
        "Blog",
        back_populates="affiliate_programs",
    )

    articles = relationship(
        "Article",
        back_populates="affiliate_program",
    )
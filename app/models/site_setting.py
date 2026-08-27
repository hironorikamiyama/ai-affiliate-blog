from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SiteSetting(Base):
    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    site_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="AI Affiliate Blog",
    )

    site_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    site_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    default_og_image: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
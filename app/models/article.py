from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    affiliate_program_id: Mapped[int] = mapped_column(
        ForeignKey("affiliate_programs.id")
    )

    title: Mapped[str] = mapped_column(String(300))
    keyword: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="draft")
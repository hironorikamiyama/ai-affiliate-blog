from sqlalchemy import Column, ForeignKey, Table

from app.db.database import Base


article_tags = Table(
    "article_tags",
    Base.metadata,
    Column(
        "article_id",
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
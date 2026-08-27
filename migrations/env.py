from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

from app.config import settings
from app.db.database import Base

from app.models.affiliate import AffiliateProgram
from app.models.article import Article
from app.models.article_image import ArticleImage
from app.models.category import Category
from app.models.tag import Tag
from app.models.article_tag import article_tags
from app.models.user import User
from app.models.site_setting import SiteSetting
from app.models.blog import Blog
from app.models.blog_membership import BlogMembership

config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    engine_kwargs = {
        "poolclass": pool.NullPool,
    }

    if settings.database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {
            "check_same_thread": False,
        }

    connectable = create_engine(
        settings.database_url,
        **engine_kwargs,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
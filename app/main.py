from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings

from app.routers import affiliate
from app.routers import article
from app.routers import article_image
from app.routers import category
from app.routers import tag
from app.routers import public_article
from app.routers import admin
from app.routers import web


app = FastAPI(
    title="AI Affiliate Blog API",
)


# ========================================
# Upload directory
# ========================================

upload_dir = Path(settings.upload_dir)

upload_dir.mkdir(
    parents=True,
    exist_ok=True,
)


# ========================================
# Static files
# ========================================

app.mount(
    "/uploads",
    StaticFiles(
        directory=str(upload_dir),
    ),
    name="uploads",
)


# ========================================
# Routers
# ========================================

app.include_router(
    affiliate.router
)

app.include_router(
    article.router
)

app.include_router(
    article_image.router
)

app.include_router(
    category.router
)

app.include_router(
    tag.router
)

app.include_router(
    public_article.router
)

app.include_router(
    admin.router
)

app.include_router(
    web.router
)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.article import Article
from app.models.category import Category
from app.models.tag import Tag
from app.schemas.article import (
    ArticleListResponse,
    ArticleResponse,
)


router = APIRouter(
    prefix="/public/articles",
    tags=["Public Articles"],
)


# ========================================
# PUBLIC ARTICLE LIST
# GET /public/articles/
# ========================================

@router.get(
    "/",
    response_model=ArticleListResponse,
)
def get_public_articles(
    category_slug: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    tag_slug: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
):
    # 公開済み記事だけを対象にする
    query = (
        db.query(Article)
        .filter(
            Article.status == "published"
        )
    )

    # ====================================
    # Category filter
    # ====================================

    if category_slug is not None:
        query = query.filter(
            Article.category.has(
                Category.slug == category_slug
            )
        )

    # ====================================
    # Tag filter
    # ====================================

    if tag_slug is not None:
        query = query.filter(
            Article.tags.any(
                Tag.slug == tag_slug
            )
        )

    total = query.count()

    articles = (
        query
        .order_by(
            Article.created_at.desc()
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "items": articles,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ========================================
# PUBLIC ARTICLE BY SLUG
# GET /public/articles/{slug}
# ========================================

@router.get(
    "/{slug}",
    response_model=ArticleResponse,
)
def get_public_article_by_slug(
    slug: str,
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(
            Article.slug == slug,
            Article.status == "published",
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Published article not found",
        )

    return article

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.article import Article
from app.schemas.article import (
    ArticleListResponse,
    ArticleResponse,
)


router = APIRouter(
    prefix="/public/articles",
    tags=["Public Articles"],
)


@router.get(
    "/",
    response_model=ArticleListResponse,
)
def get_public_articles(
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
    query = (
        db.query(Article)
        .filter(Article.status == "published")
    )

    total = query.count()

    articles = (
        query
        .order_by(Article.created_at.desc())
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
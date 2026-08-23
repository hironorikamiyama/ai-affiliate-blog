from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.affiliate import AffiliateProgram
from app.models.article import Article
from app.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticleListResponse,
    ArticleResponse,
    ArticleStatus,
)

router = APIRouter(
    prefix="/articles",
    tags=["Articles"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    response_model=ArticleResponse,
)
def create_article(
    article: ArticleCreate,
    db: Session = Depends(get_db),
):
    program = (
        db.query(AffiliateProgram)
        .filter(
            AffiliateProgram.id
            == article.affiliate_program_id
        )
        .first()
    )

    if program is None:
        raise HTTPException(
            status_code=404,
            detail="Affiliate program not found",
        )

    existing_slug = (
        db.query(Article)
        .filter(Article.slug == article.slug)
        .first()
    )

    if existing_slug is not None:
        raise HTTPException(
            status_code=409,
            detail="Article slug already exists",
        )

    db_article = Article(
        affiliate_program_id=article.affiliate_program_id,
        title=article.title,
        slug=article.slug,
        keyword=article.keyword,
        meta_description=article.meta_description,
        body=article.body,
        status=article.status.value,
    )

    db.add(db_article)
    db.commit()
    db.refresh(db_article)

    return db_article

@router.get(
    "/",
    response_model=ArticleListResponse,
)
def get_articles(
    status: ArticleStatus | None = None,
    affiliate_program_id: int | None = Query(
        default=None,
        ge=1,
    ),
    keyword: str | None = Query(
        default=None,
        min_length=1,
        max_length=200,
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
    query = db.query(Article)

    if status is not None:
        query = query.filter(
            Article.status == status.value
        )

    if affiliate_program_id is not None:
        query = query.filter(
            Article.affiliate_program_id
            == affiliate_program_id
        )

    if keyword is not None:
        query = query.filter(
            Article.keyword.contains(keyword)
        )

    total = query.count()

    articles = (
        query
        .order_by(Article.id.asc())
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
    "/{article_id}",
    response_model=ArticleResponse,
)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(Article.id == article_id)
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    return article

@router.patch(
    "/{article_id}",
    response_model=ArticleResponse,
)
def update_article(
    article_id: int,
    update_data: ArticleUpdate,
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(Article.id == article_id)
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    data = update_data.model_dump(exclude_unset=True)

    if "affiliate_program_id" in data:
        program = (
            db.query(AffiliateProgram)
            .filter(
                AffiliateProgram.id
                == data["affiliate_program_id"]
            )
            .first()
        )

        if program is None:
            raise HTTPException(
                status_code=404,
                detail="Affiliate program not found",
            )

    if "slug" in data:
        existing_slug = (
            db.query(Article)
            .filter(
                Article.slug == data["slug"],
                Article.id != article_id,
            )
            .first()
        )

        if existing_slug is not None:
            raise HTTPException(
                status_code=409,
                detail="Article slug already exists",
            )

    if "status" in data and data["status"] is not None:
        data["status"] = data["status"].value

    for field, value in data.items():
        setattr(article, field, value)

    db.commit()
    db.refresh(article)

    return article


@router.delete(
    "/{article_id}",
    status_code=204,
)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(Article.id == article_id)
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    db.delete(article)
    db.commit()


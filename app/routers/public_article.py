from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.article import Article
from app.models.blog import Blog
from app.models.category import Category
from app.models.tag import Tag
from app.schemas.article import (
    ArticleListResponse,
    ArticleResponse,
)

from app.services.affiliate_link_renderer import (
    expand_affiliate_links,
)


router = APIRouter(
    prefix="/public/articles",
    tags=["Public Articles"],
)


# ========================================
# CURRENT PUBLIC BLOG
# ========================================

def get_current_public_blog(
    db: Session,
) -> Blog:
    """
    公開APIで現在対象となる有効なBlogを取得する。

    現段階では有効なBlogのうち
    IDが最も小さいものを使用する。
    """

    blog = (
        db.query(Blog)
        .filter(
            Blog.is_active.is_(True)
        )
        .order_by(
            Blog.id.asc()
        )
        .first()
    )

    if blog is None:
        raise HTTPException(
            status_code=404,
            detail="Active blog not found",
        )

    return blog


# ========================================
# PUBLIC RESPONSE
# ========================================

def build_public_article_response(
    article: Article,
    db: Session,
) -> ArticleResponse:
    response = ArticleResponse.model_validate(
        article
    )

    return response.model_copy(
        update={
            "body": expand_affiliate_links(
                body=response.body,
                db=db,
            )
        }
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
    current_blog = get_current_public_blog(
        db=db
    )

    # ====================================
    # Published articles in current Blog
    # ====================================

    query = (
        db.query(Article)
        .filter(
            Article.blog_id == current_blog.id,
            Article.status == "published",
        )
    )

    # ====================================
    # Category filter
    # ====================================

    if category_slug is not None:
        query = query.filter(
            Article.category.has(
                and_(
                    Category.blog_id
                    == current_blog.id,
                    Category.slug
                    == category_slug,
                )
            )
        )

    # ====================================
    # Tag filter
    # ====================================

    if tag_slug is not None:
        query = query.filter(
            Article.tags.any(
                and_(
                    Tag.blog_id
                    == current_blog.id,
                    Tag.slug
                    == tag_slug,
                )
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
        "items": [
            build_public_article_response(
                article=article,
                db=db,
            )
            for article in articles
        ],
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
    current_blog = get_current_public_blog(
        db=db
    )

    article = (
        db.query(Article)
        .filter(
            Article.blog_id == current_blog.id,
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

    return build_public_article_response(
        article=article,
        db=db,
    )
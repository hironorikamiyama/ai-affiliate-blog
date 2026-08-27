from pathlib import Path

import markdown

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.article import Article
from app.models.article_image import ArticleImage
from app.services.affiliate_link_renderer import (
    expand_affiliate_links,
)
from app.services.article_image_renderer import (
    expand_article_images,
)


router = APIRouter(
    tags=["Web"],
)


# ========================================
# Templates
# ========================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


# ========================================
# BLOG ARTICLE LIST
# GET /blog
# ========================================

@router.get(
    "/blog",
    response_class=HTMLResponse,
)
def blog_article_list(
    request: Request,
    db: Session = Depends(get_db),
):
    articles = (
        db.query(Article)
        .filter(
            Article.status == "published"
        )
        .order_by(
            Article.created_at.desc()
        )
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="public/article_list.html",
        context={
            "articles": articles,
        },
    )


# ========================================
# BLOG ARTICLE DETAIL
# GET /blog/{slug}
# ========================================

@router.get(
    "/blog/{slug}",
    response_class=HTMLResponse,
)
def blog_article_detail(
    slug: str,
    request: Request,
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

    # ====================================
    # Featured Image
    # ====================================

    featured_image = (
        db.query(ArticleImage)
        .filter(
            ArticleImage.article_id
            == article.id,
            ArticleImage.is_featured.is_(
                True
            ),
        )
        .order_by(
            ArticleImage.position.asc(),
            ArticleImage.id.asc(),
        )
        .first()
    )

    # ====================================
    # Affiliate link expansion
    # ====================================

    rendered_body = expand_affiliate_links(
        body=article.body,
        db=db,
    )

    # ====================================
    # Article image expansion
    # ====================================

    rendered_body = expand_article_images(
        body=rendered_body,
        article_id=article.id,
        db=db,
    )

    # ====================================
    # Markdown -> HTML
    # ====================================

    body_html = markdown.markdown(
        rendered_body,
        extensions=[
            "extra",
            "sane_lists",
        ],
    )

    # ====================================
    # Markdown -> HTML
    # ====================================

    body_html = markdown.markdown(
        rendered_body,
        extensions=[
            "extra",
            "sane_lists",
        ],
    )

    return templates.TemplateResponse(
        request=request,
        name="public/article_detail.html",
        context={
            "article": article,
            "body_html": body_html,
            "featured_image": featured_image,
        },
    )

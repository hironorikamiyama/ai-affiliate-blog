from pathlib import Path

import markdown

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)

from fastapi.responses import (
    HTMLResponse,
    Response,
)

from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.article import Article
from app.models.article_image import ArticleImage
from app.models.blog import Blog
from app.models.site_setting import SiteSetting

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

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)

templates = Jinja2Templates(
    directory=str(
        BASE_DIR / "templates"
    )
)


# ========================================
# CURRENT PUBLIC BLOG
# ========================================

def get_current_public_blog(
    db: Session,
) -> Blog | None:
    """
    現在公開対象となっている
    有効なブログを取得する。

    現段階では有効なブログのうち
    IDが最も小さいものを使用する。
    """

    return (
        db.query(Blog)
        .filter(
            Blog.is_active.is_(True)
        )
        .order_by(
            Blog.id.asc()
        )
        .first()
    )


def get_site_setting(
    db: Session,
    blog_id: int,
) -> SiteSetting | None:
    """
    指定ブログの有効な
    SiteSettingを取得する。
    """

    return (
        db.query(SiteSetting)
        .filter(
            SiteSetting.blog_id
            == blog_id,
            SiteSetting.is_active.is_(
                True
            ),
        )
        .order_by(
            SiteSetting.id.asc()
        )
        .first()
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
    # ------------------------------------
    # Current Blog
    # ------------------------------------

    current_blog = (
        get_current_public_blog(
            db=db,
        )
    )

    if current_blog is None:
        raise HTTPException(
            status_code=404,
            detail="Active blog not found",
        )

    # ------------------------------------
    # Articles
    # ------------------------------------

    articles = (
        db.query(Article)
        .filter(
            Article.blog_id
            == current_blog.id,
            Article.status
            == "published",
        )
        .order_by(
            Article.created_at.desc()
        )
        .all()
    )

    # ------------------------------------
    # Site Settings
    # ------------------------------------

    site_setting = (
        get_site_setting(
            db=db,
            blog_id=current_blog.id,
        )
    )

    site_name = (
        site_setting.site_name
        if site_setting
        else current_blog.name
    )

    site_description = (
        site_setting.site_description
        if site_setting
        else None
    )

    site_url = (
        site_setting.site_url.rstrip("/")
        if (
            site_setting
            and site_setting.site_url
        )
        else str(
            request.base_url
        ).rstrip("/")
    )

    canonical_url = (
        f"{site_url}/blog"
    )

    default_og_image = (
        site_setting.default_og_image
        if site_setting
        else None
    )

    # ------------------------------------
    # Template
    # ------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="public/article_list.html",
        context={
            "articles": articles,
            "site_name": site_name,
            "site_description":
                site_description,
            "canonical_url":
                canonical_url,
            "default_og_image":
                default_og_image,
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
    # ------------------------------------
    # Current Blog
    # ------------------------------------

    current_blog = (
        get_current_public_blog(
            db=db,
        )
    )

    if current_blog is None:
        raise HTTPException(
            status_code=404,
            detail="Active blog not found",
        )

    # ------------------------------------
    # Article
    # ------------------------------------

    article = (
        db.query(Article)
        .filter(
            Article.blog_id
            == current_blog.id,
            Article.slug == slug,
            Article.status
            == "published",
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Published article "
                "not found"
            ),
        )

    # ------------------------------------
    # Site Settings
    # ------------------------------------

    site_setting = (
        get_site_setting(
            db=db,
            blog_id=current_blog.id,
        )
    )

    site_name = (
        site_setting.site_name
        if site_setting
        else current_blog.name
    )

    site_url = (
        site_setting.site_url.rstrip("/")
        if (
            site_setting
            and site_setting.site_url
        )
        else str(
            request.base_url
        ).rstrip("/")
    )

    default_og_image = (
        site_setting.default_og_image
        if site_setting
        else None
    )

    # ------------------------------------
    # Featured Image
    # ------------------------------------

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

    # ------------------------------------
    # OGP Image
    # ------------------------------------

    if featured_image:
        og_image_url = str(
            request.url_for(
                "uploads",
                path=(
                    featured_image.image_url
                    .replace(
                        "/uploads/",
                        "",
                        1,
                    )
                ),
            )
        )

    else:
        og_image_url = (
            default_og_image
        )

    # ------------------------------------
    # Affiliate Link Expansion
    # ------------------------------------

    rendered_body = (
        expand_affiliate_links(
            body=article.body,
            db=db,
        )
    )

    # ------------------------------------
    # Article Image Expansion
    # ------------------------------------

    rendered_body = (
        expand_article_images(
            body=rendered_body,
            article_id=article.id,
            db=db,
        )
    )

    # ------------------------------------
    # Markdown -> HTML
    # ------------------------------------

    body_html = markdown.markdown(
        rendered_body,
        extensions=[
            "extra",
            "sane_lists",
        ],
    )

    # ------------------------------------
    # Canonical URL
    # ------------------------------------

    canonical_url = (
        f"{site_url}/blog/"
        f"{article.slug}"
    )

    # ------------------------------------
    # Template
    # ------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="public/article_detail.html",
        context={
            "article": article,
            "body_html": body_html,
            "featured_image":
                featured_image,
            "site_name": site_name,
            "canonical_url":
                canonical_url,
            "og_image_url":
                og_image_url,
        },
    )


# ========================================
# SITEMAP
# GET /sitemap.xml
# ========================================

@router.get(
    "/sitemap.xml",
    response_class=Response,
)
def sitemap(
    request: Request,
    db: Session = Depends(get_db),
):
    # ------------------------------------
    # Current Blog
    # ------------------------------------

    current_blog = (
        get_current_public_blog(
            db=db,
        )
    )

    if current_blog is None:
        raise HTTPException(
            status_code=404,
            detail="Active blog not found",
        )

    # ------------------------------------
    # Site Settings
    # ------------------------------------

    site_setting = (
        get_site_setting(
            db=db,
            blog_id=current_blog.id,
        )
    )

    site_url = (
        site_setting.site_url.rstrip("/")
        if (
            site_setting
            and site_setting.site_url
        )
        else str(
            request.base_url
        ).rstrip("/")
    )

    # ------------------------------------
    # Articles
    # ------------------------------------

    articles = (
        db.query(Article)
        .filter(
            Article.blog_id
            == current_blog.id,
            Article.status
            == "published",
        )
        .order_by(
            Article.created_at.desc()
        )
        .all()
    )

    # ------------------------------------
    # URLs
    # ------------------------------------

    urls: list[str] = []

    urls.append(
        f"""
    <url>
        <loc>{site_url}/blog</loc>
    </url>
        """.strip()
    )

    for article in articles:
        urls.append(
            f"""
    <url>
        <loc>{site_url}/blog/{article.slug}</loc>
    </url>
            """.strip()
        )

    # ------------------------------------
    # XML
    # ------------------------------------

    xml = (
        '<?xml version="1.0" '
        'encoding="UTF-8"?>\n'
        '<urlset '
        'xmlns="http://www.sitemaps.org/'
        'schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>"
    )

    return Response(
        content=xml,
        media_type="application/xml",
    )


# ========================================
# ROBOTS.TXT
# GET /robots.txt
# ========================================

@router.get(
    "/robots.txt",
    response_class=Response,
)
def robots_txt(
    request: Request,
    db: Session = Depends(get_db),
):
    # ------------------------------------
    # Current Blog
    # ------------------------------------

    current_blog = (
        get_current_public_blog(
            db=db,
        )
    )

    if current_blog is None:
        raise HTTPException(
            status_code=404,
            detail="Active blog not found",
        )

    # ------------------------------------
    # Site Settings
    # ------------------------------------

    site_setting = (
        get_site_setting(
            db=db,
            blog_id=current_blog.id,
        )
    )

    site_url = (
        site_setting.site_url.rstrip("/")
        if (
            site_setting
            and site_setting.site_url
        )
        else str(
            request.base_url
        ).rstrip("/")
    )

    # ------------------------------------
    # robots.txt
    # ------------------------------------

    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin/\n"
        "\n"
        f"Sitemap: "
        f"{site_url}/sitemap.xml\n"
    )

    return Response(
        content=content,
        media_type="text/plain",
    )
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)


from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.models.affiliate import AffiliateProgram
from app.models.article import Article
from app.models.article_image import ArticleImage
from app.models.category import Category
from app.models.tag import Tag
from app.services.ai_writer import generate_article
from app.services.seo_analyzer import analyze_seo
from app.services.seo_rewriter import rewrite_article_for_seo

from pathlib import Path
from uuid import uuid4


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


templates = Jinja2Templates(
    directory="templates"
)


ADMIN_ARTICLE_UPLOAD_DIR = (
    Path(settings.upload_dir)
    / "articles"
)

ADMIN_ARTICLE_UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_IMAGE_FILE_SIZE = (
    5 * 1024 * 1024
)

# ========================================
# ARTICLE LIST
# GET /admin/articles
# ========================================

@router.get(
    "/articles",
    response_class=HTMLResponse,
)
def admin_article_list(
    request: Request,
    db: Session = Depends(get_db),
):
    articles = (
        db.query(Article)
        .order_by(
            Article.updated_at.desc()
        )
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/articles.html",
        context={
            "articles": articles,
        },
    )


# ========================================
# ARTICLE EDIT FORM
# GET /admin/articles/{article_id}/edit
# ========================================

@router.get(
    "/articles/{article_id}/edit",
    response_class=HTMLResponse,
)
def admin_article_edit(
    article_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(
            Article.id == article_id
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    categories = (
        db.query(Category)
        .order_by(
            Category.name.asc()
        )
        .all()
    )

    images = (
        db.query(ArticleImage)
        .filter(
            ArticleImage.article_id
            == article_id
        )
        .order_by(
            ArticleImage.position.asc(),
            ArticleImage.id.asc(),
        )
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/article_edit.html",
        context={
            "article": article,
            "categories": categories,
            "images": images,
            "seo_result": None,
            "rewrite_result": None,
        },
    )


# ========================================
# ARTICLE UPDATE
# POST /admin/articles/{article_id}/edit
#
# 通常の記事編集のみ。
# status変更はpublish/draft専用APIで行う。
# ========================================

@router.post(
    "/articles/{article_id}/edit",
)
def admin_article_update(
    article_id: int,
    title: str = Form(...),
    slug: str = Form(...),
    keyword: str = Form(...),
    meta_description: str = Form(""),
    body: str = Form(...),
    category_id: str = Form(""),
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(
            Article.id == article_id
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    # ------------------------------------
    # slug duplicate check
    # ------------------------------------

    existing_slug = (
        db.query(Article)
        .filter(
            Article.slug == slug,
            Article.id != article_id,
        )
        .first()
    )

    if existing_slug is not None:
        raise HTTPException(
            status_code=409,
            detail="Article slug already exists",
        )

    article.title = title
    article.slug = slug
    article.keyword = keyword
    article.meta_description = (
        meta_description or None
    )
    article.body = body

    # ------------------------------------
    # Category
    # ------------------------------------

    if category_id:
        try:
            category_id_value = int(
                category_id
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid category id",
            ) from exc

        category = (
            db.query(Category)
            .filter(
                Category.id
                == category_id_value
            )
            .first()
        )

        if category is None:
            raise HTTPException(
                status_code=404,
                detail="Category not found",
            )

        article.category_id = (
            category.id
        )

    else:
        article.category_id = None

    try:
        db.commit()
        db.refresh(article)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Article conflicts with existing data",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to update article",
        )

    return RedirectResponse(
        url=f"/admin/articles/{article.id}/edit",
        status_code=303,
    )


# ========================================
# Article Image Upload
# POST /admin/articles/{article_id}/images
# ========================================

@router.post(
    "/articles/{article_id}/images",
)
async def admin_article_image_upload(
    article_id: int,
    file: UploadFile = File(...),
    alt_text: str = Form(""),
    caption: str = Form(""),
    position: int = Form(0),
    is_featured: bool = Form(False),
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(
            Article.id == article_id
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    if (
        file.content_type
        not in ALLOWED_IMAGE_CONTENT_TYPES
    ):
        raise HTTPException(
            status_code=415,
            detail=(
                "Only JPEG, PNG, and WebP "
                "images are allowed"
            ),
        )

    try:
        file_data = await file.read()

    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to read uploaded image",
        ) from exc

    if len(file_data) > MAX_IMAGE_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                "Image file is too large. "
                "Maximum size is 5MB"
            ),
        )

    extension = (
        ALLOWED_IMAGE_CONTENT_TYPES[
            file.content_type
        ]
    )

    stored_filename = (
        f"{uuid4().hex}{extension}"
    )

    article_directory = (
        ADMIN_ARTICLE_UPLOAD_DIR
        / str(article_id)
    )

    file_path = (
        article_directory
        / stored_filename
    )

    try:
        article_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            file_path,
            "wb",
        ) as buffer:
            buffer.write(file_data)

    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to save image file",
        ) from exc

    try:
        if is_featured:
            (
                db.query(ArticleImage)
                .filter(
                    ArticleImage.article_id
                    == article_id,
                    ArticleImage.is_featured.is_(
                        True
                    ),
                )
                .update(
                    {
                        ArticleImage.is_featured:
                        False
                    },
                    synchronize_session=False,
                )
            )

        image = ArticleImage(
            article_id=article_id,
            file_path=str(file_path),
            original_filename=(
                file.filename
                or stored_filename
            ),
            alt_text=(
                alt_text or None
            ),
            caption=(
                caption or None
            ),
            position=position,
            is_featured=is_featured,
        )

        db.add(image)
        db.commit()

    except IntegrityError as exc:
        db.rollback()

        try:
            if file_path.exists():
                file_path.unlink()

        except OSError:
            pass

        raise HTTPException(
            status_code=409,
            detail=(
                "Article image conflicts "
                "with existing data"
            ),
        ) from exc

    except SQLAlchemyError as exc:
        db.rollback()

        try:
            if file_path.exists():
                file_path.unlink()

        except OSError:
            pass

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save article "
                "image information"
            ),
        ) from exc

    return RedirectResponse(
        url=(
            f"/admin/articles/"
            f"{article_id}/edit"
        ),
        status_code=303,
    )

# ========================================
# Article Image Update
# POST /admin/articles/{article_id}/images/{image_id}/edit
# ========================================

@router.post(
    "/articles/{article_id}/images/{image_id}/edit",
)
def admin_article_image_update(
    article_id: int,
    image_id: int,
    alt_text: str = Form(""),
    caption: str = Form(""),
    position: int = Form(0),
    is_featured: bool = Form(False),
    db: Session = Depends(get_db),
):
    image = (
        db.query(ArticleImage)
        .filter(
            ArticleImage.id == image_id,
            ArticleImage.article_id == article_id,
        )
        .first()
    )

    if image is None:
        raise HTTPException(
            status_code=404,
            detail="Article image not found",
        )

    try:
        if is_featured:
            (
                db.query(ArticleImage)
                .filter(
                    ArticleImage.article_id
                    == article_id,
                    ArticleImage.id
                    != image_id,
                    ArticleImage.is_featured.is_(
                        True
                    ),
                )
                .update(
                    {
                        ArticleImage.is_featured:
                        False
                    },
                    synchronize_session=False,
                )
            )

        image.alt_text = (
            alt_text or None
        )

        image.caption = (
            caption or None
        )

        image.position = position

        image.is_featured = (
            is_featured
        )

        db.commit()
        db.refresh(image)

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Article image conflicts "
                "with existing data"
            ),
        ) from exc

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to update "
                "article image"
            ),
        ) from exc

    return RedirectResponse(
        url=(
            f"/admin/articles/"
            f"{article_id}/edit"
        ),
        status_code=303,
    )

# ========================================
# Article Image Delete
# POST /admin/articles/{article_id}/images/{image_id}/delete
# ========================================

@router.post(
    "/articles/{article_id}/images/{image_id}/delete",
)
def admin_article_image_delete(
    article_id: int,
    image_id: int,
    db: Session = Depends(get_db),
):
    image = (
        db.query(ArticleImage)
        .filter(
            ArticleImage.id == image_id,
            ArticleImage.article_id == article_id,
        )
        .first()
    )

    if image is None:
        raise HTTPException(
            status_code=404,
            detail="Article image not found",
        )

    file_path = Path(
        image.file_path
    )

    try:
        db.delete(image)
        db.commit()

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Article image is referenced "
                "by other data"
            ),
        ) from exc

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to delete "
                "article image"
            ),
        ) from exc

    try:
        if file_path.exists():
            file_path.unlink()

    except OSError:
        pass

    return RedirectResponse(
        url=(
            f"/admin/articles/"
            f"{article_id}/edit"
        ),
        status_code=303,
    )

# ========================================
# ARTICLE SEO ANALYSIS
# POST /admin/articles/{article_id}/seo
# ========================================

@router.post(
    "/articles/{article_id}/seo",
    response_class=HTMLResponse,
)
def admin_article_seo_analysis(
    article_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    # ------------------------------------
    # Article
    # ------------------------------------

    article = (
        db.query(Article)
        .filter(
            Article.id == article_id
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    # ------------------------------------
    # Categories
    #
    # SEO分析後も同じ編集画面を
    # 再表示するため必要
    # ------------------------------------

    categories = (
        db.query(Category)
        .order_by(
            Category.name.asc()
        )
        .all()
    )

    images = (
        db.query(ArticleImage)
        .filter(
            ArticleImage.article_id
            == article_id
        )
        .order_by(
            ArticleImage.position.asc(),
            ArticleImage.id.asc(),
        )
        .all()
    )

    # ------------------------------------
    # SEO Analysis
    # ------------------------------------

    try:
        seo_result = analyze_seo(
            title=article.title,
            keyword=article.keyword,
            meta_description=(
                article.meta_description
            ),
            body=article.body,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to analyze SEO: "
                f"{exc}"
            ),
        ) from exc

    # ------------------------------------
    # Return edit page
    # ------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="admin/article_edit.html",
        context={
            "article": article,
            "categories": categories,
            "images": images,
            "seo_result": seo_result,
            "rewrite_result": None,
        },
    )

# ========================================
# ARTICLE SEO REWRITE
# POST /admin/articles/{article_id}/seo/rewrite
# ========================================

@router.post(
    "/articles/{article_id}/seo/rewrite",
    response_class=HTMLResponse,
)
def admin_article_seo_rewrite(
    article_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    # ------------------------------------
    # Article
    # ------------------------------------

    article = (
        db.query(Article)
        .filter(
            Article.id == article_id
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    # ------------------------------------
    # Categories
    #
    # 同じ編集画面を再表示するため必要
    # ------------------------------------

    categories = (
        db.query(Category)
        .order_by(
            Category.name.asc()
        )
        .all()
    )

    images = (
        db.query(ArticleImage)
        .filter(
            ArticleImage.article_id
            == article_id
        )
        .order_by(
            ArticleImage.position.asc(),
            ArticleImage.id.asc(),
        )
        .all()
    )

    # ------------------------------------
    # SEO Analysis
    #
    # リライト結果と一緒に
    # SEO分析結果も再表示する
    # ------------------------------------

    try:
        seo_result = analyze_seo(
            title=article.title,
            keyword=article.keyword,
            meta_description=(
                article.meta_description
            ),
            body=article.body,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to analyze SEO: "
                f"{exc}"
            ),
        ) from exc

    # ------------------------------------
    # SEO Rewrite
    #
    # DBは更新しない
    # ------------------------------------

    try:
        rewrite_result = (
            rewrite_article_for_seo(
                title=article.title,
                keyword=article.keyword,
                meta_description=(
                    article.meta_description
                ),
                body=article.body,
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to rewrite article: "
                f"{exc}"
            ),
        ) from exc

    # ------------------------------------
    # Return edit page
    # ------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="admin/article_edit.html",
        context={
            "article": article,
            "categories": categories,
            "images": images,
            "seo_result": seo_result,
            "rewrite_result": rewrite_result,
        },
    )


# ========================================
# APPLY SEO REWRITE
# POST /admin/articles/{article_id}/seo/rewrite/apply
# ========================================

@router.post(
    "/articles/{article_id}/seo/rewrite/apply",
)
def admin_article_apply_seo_rewrite(
    article_id: int,
    rewritten_body: str = Form(...),
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(
            Article.id == article_id
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    rewritten_body = rewritten_body.strip()

    if not rewritten_body:
        raise HTTPException(
            status_code=400,
            detail="Rewritten body is empty",
        )

    current_body = article.body.strip()

    if rewritten_body == current_body:
        return RedirectResponse(
            url=f"/admin/articles/{article.id}/edit",
            status_code=303,
        )

    article.body = rewritten_body

    try:
        db.commit()
        db.refresh(article)

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to apply SEO rewrite",
        ) from exc

    return RedirectResponse(
        url=f"/admin/articles/{article.id}/edit",
        status_code=303,
    )


@router.post(
    "/articles/{article_id}/seo/apply-title",
)
def admin_article_apply_seo_title(
    article_id: int,
    title_suggestion: str = Form(...),
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(
            Article.id == article_id
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    title_suggestion = (
        title_suggestion.strip()
    )

    if not title_suggestion:
        raise HTTPException(
            status_code=400,
            detail="Title suggestion is empty",
        )

    article.title = title_suggestion

    try:
        db.commit()
        db.refresh(article)

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to apply SEO title",
        ) from exc

    return RedirectResponse(
        url=f"/admin/articles/{article.id}/edit",
        status_code=303,
    )


@router.post(
    "/articles/{article_id}/seo/apply-meta-description",
)
def admin_article_apply_seo_meta_description(
    article_id: int,
    meta_description_suggestion: str = Form(...),
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(
            Article.id == article_id
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    meta_description_suggestion = (
        meta_description_suggestion.strip()
    )

    if not meta_description_suggestion:
        raise HTTPException(
            status_code=400,
            detail="Meta Description suggestion is empty",
        )

    article.meta_description = (
        meta_description_suggestion
    )

    try:
        db.commit()
        db.refresh(article)

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to apply SEO Meta Description",
        ) from exc

    return RedirectResponse(
        url=f"/admin/articles/{article.id}/edit",
        status_code=303,
    )

# ========================================
# PUBLISH ARTICLE
# POST /admin/articles/{article_id}/publish
# ========================================

@router.post(
    "/articles/{article_id}/publish",
)
def admin_article_publish(
    article_id: int,
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(
            Article.id == article_id
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    article.status = "published"

    try:
        db.commit()
        db.refresh(article)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to publish article",
        )

    return RedirectResponse(
        url=f"/admin/articles/{article.id}/edit",
        status_code=303,
    )


# ========================================
# MOVE ARTICLE TO DRAFT
# POST /admin/articles/{article_id}/draft
# ========================================

@router.post(
    "/articles/{article_id}/draft",
)
def admin_article_to_draft(
    article_id: int,
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(
            Article.id == article_id
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    article.status = "draft"

    try:
        db.commit()
        db.refresh(article)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to move article to draft",
        )

    return RedirectResponse(
        url=f"/admin/articles/{article.id}/edit",
        status_code=303,
    )


# ========================================
# ARTICLE GENERATE FORM
# GET /admin/articles/generate
# ========================================

@router.get(
    "/articles/generate",
    response_class=HTMLResponse,
)
def admin_article_generate_form(
    request: Request,
    db: Session = Depends(get_db),
):
    affiliate_programs = (
        db.query(AffiliateProgram)
        .order_by(
            AffiliateProgram.name.asc()
        )
        .all()
    )

    categories = (
        db.query(Category)
        .order_by(
            Category.name.asc()
        )
        .all()
    )

    tags = (
        db.query(Tag)
        .order_by(
            Tag.name.asc()
        )
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/article_generate.html",
        context={
            "affiliate_programs": affiliate_programs,
            "categories": categories,
            "tags": tags,
        },
    )


# ========================================
# ARTICLE GENERATE
# POST /admin/articles/generate
# ========================================

@router.post(
    "/articles/generate",
)
def admin_article_generate(
    affiliate_program_id: int = Form(...),
    keyword: str = Form(...),
    category_id: int = Form(...),
    tag_ids: list[int] = Form(
        default=[]
    ),
    db: Session = Depends(get_db),
):
    # ------------------------------------
    # AffiliateProgram
    # ------------------------------------

    program = (
        db.query(AffiliateProgram)
        .filter(
            AffiliateProgram.id
            == affiliate_program_id
        )
        .first()
    )

    if program is None:
        raise HTTPException(
            status_code=404,
            detail="Affiliate program not found",
        )

    # ------------------------------------
    # Category
    # ------------------------------------

    category = (
        db.query(Category)
        .filter(
            Category.id == category_id
        )
        .first()
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    # ------------------------------------
    # Tags
    # ------------------------------------

    tags = []

    if tag_ids:
        unique_tag_ids = list(
            dict.fromkeys(
                tag_ids
            )
        )

        tags = (
            db.query(Tag)
            .filter(
                Tag.id.in_(
                    unique_tag_ids
                )
            )
            .all()
        )

        found_tag_ids = {
            tag.id
            for tag in tags
        }

        missing_tag_ids = [
            tag_id
            for tag_id in unique_tag_ids
            if tag_id
            not in found_tag_ids
        ]

        if missing_tag_ids:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Tag not found: "
                    f"{missing_tag_ids}"
                ),
            )

    # ------------------------------------
    # AI / Mock generation
    # ------------------------------------

    try:
        generated = generate_article(
            program=program,
            keyword=keyword,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Failed to generate article: "
                f"{exc}"
            ),
        ) from exc

    # ------------------------------------
    # slug duplicate check
    # ------------------------------------

    existing_slug = (
        db.query(Article)
        .filter(
            Article.slug
            == generated["slug"]
        )
        .first()
    )

    if existing_slug is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Generated article slug "
                "already exists"
            ),
        )

    # ------------------------------------
    # Create draft article
    # ------------------------------------

    article = Article(
        affiliate_program_id=(
            affiliate_program_id
        ),
        category_id=category_id,
        title=generated["title"],
        slug=generated["slug"],
        keyword=keyword,
        meta_description=(
            generated[
                "meta_description"
            ]
        ),
        body=generated["body"],
        status="draft",
    )

    article.tags = tags

    try:
        db.add(article)
        db.commit()
        db.refresh(article)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Generated article conflicts "
                "with existing data"
            ),
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save "
                "generated article"
            ),
        )

    return RedirectResponse(
        url=(
            f"/admin/articles/"
            f"{article.id}/edit"
        ),
        status_code=303,
    )

# ========================================
# AFFILIATE PROGRAM LIST
# GET /admin/affiliate-programs
# ========================================

@router.get(
    "/affiliate-programs",
    response_class=HTMLResponse,
)
def admin_affiliate_program_list(
    request: Request,
    db: Session = Depends(get_db),
):
    programs = (
        db.query(AffiliateProgram)
        .order_by(
            AffiliateProgram.updated_at.desc()
        )
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/affiliate_programs.html",
        context={
            "programs": programs,
        },
    )


# ========================================
# AFFILIATE PROGRAM CREATE FORM
# GET /admin/affiliate-programs/new
# ========================================

@router.get(
    "/affiliate-programs/new",
    response_class=HTMLResponse,
)
def admin_affiliate_program_create_form(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="admin/affiliate_program_form.html",
        context={
            "program": None,
        },
    )


# ========================================
# AFFILIATE PROGRAM CREATE
# POST /admin/affiliate-programs/new
# ========================================

@router.post(
    "/affiliate-programs/new",
)
def admin_affiliate_program_create(
    name: str = Form(...),
    asp_name: str = Form(...),
    affiliate_url: str = Form(...),
    category: str = Form(...),
    reward_amount: str = Form(""),
    reward_type: str = Form("fixed"),
    status: str = Form("active"),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    reward_amount_value = None

    if reward_amount:
        try:
            reward_amount_value = float(
                reward_amount
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid reward amount",
            ) from exc

    program = AffiliateProgram(
        name=name,
        asp_name=asp_name,
        affiliate_url=affiliate_url,
        category=category,
        reward_amount=reward_amount_value,
        reward_type=reward_type,
        status=status,
        description=description or None,
    )

    try:
        db.add(program)
        db.commit()
        db.refresh(program)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to create affiliate program",
        )

    return RedirectResponse(
        url="/admin/affiliate-programs",
        status_code=303,
    )


# ========================================
# AFFILIATE PROGRAM EDIT FORM
# GET /admin/affiliate-programs/{program_id}/edit
# ========================================

@router.get(
    "/affiliate-programs/{program_id}/edit",
    response_class=HTMLResponse,
)
def admin_affiliate_program_edit_form(
    program_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    program = (
        db.query(AffiliateProgram)
        .filter(
            AffiliateProgram.id == program_id
        )
        .first()
    )

    if program is None:
        raise HTTPException(
            status_code=404,
            detail="Affiliate program not found",
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/affiliate_program_form.html",
        context={
            "program": program,
        },
    )


# ========================================
# AFFILIATE PROGRAM UPDATE
# POST /admin/affiliate-programs/{program_id}/edit
# ========================================

@router.post(
    "/affiliate-programs/{program_id}/edit",
)
def admin_affiliate_program_update(
    program_id: int,
    name: str = Form(...),
    asp_name: str = Form(...),
    affiliate_url: str = Form(...),
    category: str = Form(...),
    reward_amount: str = Form(""),
    reward_type: str = Form("fixed"),
    status: str = Form("active"),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    program = (
        db.query(AffiliateProgram)
        .filter(
            AffiliateProgram.id == program_id
        )
        .first()
    )

    if program is None:
        raise HTTPException(
            status_code=404,
            detail="Affiliate program not found",
        )

    reward_amount_value = None

    if reward_amount:
        try:
            reward_amount_value = float(
                reward_amount
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid reward amount",
            ) from exc

    program.name = name
    program.asp_name = asp_name
    program.affiliate_url = affiliate_url
    program.category = category
    program.reward_amount = reward_amount_value
    program.reward_type = reward_type
    program.status = status
    program.description = description or None

    try:
        db.commit()
        db.refresh(program)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to update affiliate program",
        )

    return RedirectResponse(
        url="/admin/affiliate-programs",
        status_code=303,
    )
    
# ========================================
# AFFILIATE PROGRAM DELETE
# POST /admin/affiliate-programs/{program_id}/delete
# ========================================

@router.post(
    "/affiliate-programs/{program_id}/delete",
)
def admin_affiliate_program_delete(
    program_id: int,
    db: Session = Depends(get_db),
):
    program = (
        db.query(AffiliateProgram)
        .filter(
            AffiliateProgram.id == program_id
        )
        .first()
    )

    if program is None:
        raise HTTPException(
            status_code=404,
            detail="Affiliate program not found",
        )

    linked_article = (
        db.query(Article)
        .filter(
            Article.affiliate_program_id == program_id
        )
        .first()
    )

    if linked_article is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Affiliate program is used by articles "
                "and cannot be deleted"
            ),
        )

    try:
        db.delete(program)
        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to delete affiliate program",
        )

    return RedirectResponse(
        url="/admin/affiliate-programs",
        status_code=303,
    )
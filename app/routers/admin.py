from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.affiliate import AffiliateProgram
from app.models.article import Article
from app.models.category import Category
from app.models.tag import Tag
from app.services.ai_writer import generate_article


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


templates = Jinja2Templates(
    directory="templates"
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

    return templates.TemplateResponse(
        request=request,
        name="admin/article_edit.html",
        context={
            "article": article,
            "categories": categories,
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
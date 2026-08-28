from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db

from app.models.affiliate import AffiliateProgram
from app.models.article import Article
from app.models.blog import Blog
from app.models.category import Category
from app.models.tag import Tag

from app.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticleListResponse,
    ArticleResponse,
    ArticleStatus,
    SimilarArticleResponse,
    ArticleGenerateRequest,
)

from app.services.article_similarity import (
    get_similar_articles,
)

from app.services.article_embedding import (
    get_embedding_similar_articles,
)

from app.services.ai_writer import generate_article


router = APIRouter(
    prefix="/articles",
    tags=["Articles"],
)


# ========================================
# CURRENT BLOG
# ========================================

def get_current_blog(
    db: Session,
) -> Blog:
    """
    現在対象となっている有効なBlogを取得する。

    現段階では有効なBlogのうち
    IDが最も小さいものを使用する。

    public側のcurrent blog判定と
    同じルールを使用する。
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
# CREATE
# POST /articles/
# ========================================

@router.post(
    "/",
    response_model=ArticleResponse,
)
def create_article(
    article: ArticleCreate,
    db: Session = Depends(get_db),
):
    current_blog = get_current_blog(
        db=db,
    )

    # ------------------------------------
    # AffiliateProgramの存在確認
    #
    # current_blogに属するAffiliateProgramのみ許可
    # ------------------------------------

    program = (
        db.query(AffiliateProgram)
        .filter(
            AffiliateProgram.id
            == article.affiliate_program_id,
            AffiliateProgram.blog_id
            == current_blog.id,
        )
        .first()
    )

    if program is None:
        raise HTTPException(
            status_code=404,
            detail="Affiliate program not found",
        )

    # ------------------------------------
    # Categoryの存在確認
    #
    # current_blogに属するCategoryのみ許可
    # ------------------------------------

    if article.category_id is not None:
        category = (
            db.query(Category)
            .filter(
                Category.id
                == article.category_id,
                Category.blog_id
                == current_blog.id,
            )
            .first()
        )

        if category is None:
            raise HTTPException(
                status_code=404,
                detail="Category not found",
            )

    # ------------------------------------
    # Tagの存在確認
    #
    # current_blogに属するTagのみ許可
    # ------------------------------------

    tags = []

    if article.tag_ids:
        unique_tag_ids = list(
            dict.fromkeys(
                article.tag_ids
            )
        )

        tags = (
            db.query(Tag)
            .filter(
                Tag.id.in_(
                    unique_tag_ids
                ),
                Tag.blog_id
                == current_blog.id,
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
            if tag_id not in found_tag_ids
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
    # slug重複確認
    #
    # Article.slugは現在Model上で
    # global UNIQUEなので、
    # 現段階では全Blogを対象に確認する。
    # ------------------------------------

    existing_slug = (
        db.query(Article)
        .filter(
            Article.slug
            == article.slug
        )
        .first()
    )

    if existing_slug is not None:
        raise HTTPException(
            status_code=409,
            detail="Article slug already exists",
        )

    # ------------------------------------
    # Article生成
    # ------------------------------------

    db_article = Article(
        blog_id=current_blog.id,
        affiliate_program_id=(
            article.affiliate_program_id
        ),
        category_id=article.category_id,
        title=article.title,
        slug=article.slug,
        keyword=article.keyword,
        meta_description=(
            article.meta_description
        ),
        body=article.body,
        status=article.status.value,
    )

    # Many-to-Many
    db_article.tags = tags

    try:
        db.add(db_article)
        db.commit()
        db.refresh(db_article)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Article conflicts "
                "with existing data"
            ),
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to create article",
        )

    return db_article


# ========================================
# LIST
# GET /articles/
# ========================================

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
    current_blog = get_current_blog(
        db=db,
    )

    query = (
        db.query(Article)
        .filter(
            Article.blog_id
            == current_blog.id
        )
    )

    if status is not None:
        query = query.filter(
            Article.status
            == status.value
        )

    if affiliate_program_id is not None:
        query = query.filter(
            Article.affiliate_program_id
            == affiliate_program_id
        )

    if keyword is not None:
        query = query.filter(
            Article.keyword.contains(
                keyword
            )
        )

    total = query.count()

    articles = (
        query
        .order_by(
            Article.id.asc()
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
# GET BY SLUG
# GET /articles/slug/{slug}
#
# IMPORTANT:
# /{article_id}/similar より前に定義する
# ========================================

@router.get(
    "/slug/{slug}",
    response_model=ArticleResponse,
)
def get_article_by_slug(
    slug: str,
    db: Session = Depends(get_db),
):
    current_blog = get_current_blog(
        db=db,
    )

    article = (
        db.query(Article)
        .filter(
            Article.slug == slug,
            Article.blog_id
            == current_blog.id,
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    return article


# ========================================
# GET BY similar
# GET /{article_id}/similar
#
# IMPORTANT:
# /{article_id}/similar/embedding より前に定義する
# ========================================

@router.get(
    "/{article_id}/similar",
    response_model=list[
        SimilarArticleResponse
    ],
)
def get_article_similarities(
    article_id: int,
    limit: int = Query(
        default=5,
        ge=1,
        le=20,
    ),
    db: Session = Depends(get_db),
):
    current_blog = get_current_blog(
        db=db,
    )

    # ------------------------------------
    # 対象記事
    # ------------------------------------

    target_article = (
        db.query(Article)
        .filter(
            Article.id == article_id,
            Article.blog_id
            == current_blog.id,
        )
        .first()
    )

    if target_article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    # ------------------------------------
    # 類似度比較対象も同一Blogのみ
    # ------------------------------------

    articles = (
        db.query(Article)
        .filter(
            Article.blog_id
            == current_blog.id
        )
        .order_by(
            Article.id.asc()
        )
        .all()
    )

    return get_similar_articles(
        target_article=target_article,
        articles=articles,
        limit=limit,
    )


# ========================================
# GET BY similar
# GET /{article_id}/similar/embedding
#
# IMPORTANT:
# /{article_id} より前に定義する
# ========================================

@router.get(
    "/{article_id}/similar/embedding",
    response_model=list[
        SimilarArticleResponse
    ],
)
def get_article_embedding_similarities(
    article_id: int,
    limit: int = Query(
        default=5,
        ge=1,
        le=20,
    ),
    min_similarity: float = Query(
        default=0.3,
        ge=0.0,
        le=1.0,
    ),
    db: Session = Depends(get_db),
):
    current_blog = get_current_blog(
        db=db,
    )

    # ------------------------------------
    # 対象記事
    # ------------------------------------

    target_article = (
        db.query(Article)
        .filter(
            Article.id == article_id,
            Article.blog_id
            == current_blog.id,
        )
        .first()
    )

    if target_article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    # ------------------------------------
    # Embedding比較対象も同一Blogのみ
    # ------------------------------------

    articles = (
        db.query(Article)
        .filter(
            Article.blog_id
            == current_blog.id
        )
        .order_by(
            Article.id.asc()
        )
        .all()
    )

    return get_embedding_similar_articles(
        target_article=target_article,
        articles=articles,
        limit=limit,
        min_similarity=min_similarity,
    )


# ========================================
# AI GENERATE
# POST /articles/generate
# ========================================

@router.post(
    "/generate",
    response_model=ArticleResponse,
)
def generate_article_draft(
    request: ArticleGenerateRequest,
    db: Session = Depends(get_db),
):
    current_blog = get_current_blog(
        db=db,
    )

    # ------------------------------------
    # AffiliateProgramの存在確認
    #
    # current_blogに属するAffiliateProgramのみ許可
    # ------------------------------------

    program = (
        db.query(AffiliateProgram)
        .filter(
            AffiliateProgram.id
            == request.affiliate_program_id,
            AffiliateProgram.blog_id
            == current_blog.id,
        )
        .first()
    )

    if program is None:
        raise HTTPException(
            status_code=404,
            detail="Affiliate program not found",
        )

    # ------------------------------------
    # Categoryの存在確認
    # ------------------------------------

    if request.category_id is not None:
        category = (
            db.query(Category)
            .filter(
                Category.id
                == request.category_id,
                Category.blog_id
                == current_blog.id,
            )
            .first()
        )

        if category is None:
            raise HTTPException(
                status_code=404,
                detail="Category not found",
            )

    # ------------------------------------
    # Tagの存在確認
    # ------------------------------------

    tags = []

    if request.tag_ids:
        unique_tag_ids = list(
            dict.fromkeys(
                request.tag_ids
            )
        )

        tags = (
            db.query(Tag)
            .filter(
                Tag.id.in_(
                    unique_tag_ids
                ),
                Tag.blog_id
                == current_blog.id,
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
            if tag_id not in found_tag_ids
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
    # AI記事生成
    # ------------------------------------

    try:
        generated = generate_article(
            program=program,
            keyword=request.keyword,
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
    # slug重複確認
    #
    # Article.slugはglobal UNIQUEのため
    # 全Blogを対象に確認する。
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
    # Article生成
    # ------------------------------------

    db_article = Article(
        blog_id=current_blog.id,
        affiliate_program_id=(
            request.affiliate_program_id
        ),
        category_id=request.category_id,
        title=generated["title"],
        slug=generated["slug"],
        keyword=request.keyword,
        meta_description=(
            generated["meta_description"]
        ),
        body=generated["body"],
        status=ArticleStatus.draft.value,
    )

    db_article.tags = tags

    try:
        db.add(db_article)
        db.commit()
        db.refresh(db_article)

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

    return db_article


# ========================================
# GET BY ID
# GET /articles/{article_id}
# ========================================

@router.get(
    "/{article_id}",
    response_model=ArticleResponse,
)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
):
    current_blog = get_current_blog(
        db=db,
    )

    article = (
        db.query(Article)
        .filter(
            Article.id == article_id,
            Article.blog_id
            == current_blog.id,
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    return article


# ========================================
# UPDATE
# PATCH /articles/{article_id}
# ========================================

@router.patch(
    "/{article_id}",
    response_model=ArticleResponse,
)
def update_article(
    article_id: int,
    update_data: ArticleUpdate,
    db: Session = Depends(get_db),
):
    current_blog = get_current_blog(
        db=db,
    )

    # ------------------------------------
    # current_blogの記事だけ取得
    # ------------------------------------

    article = (
        db.query(Article)
        .filter(
            Article.id == article_id,
            Article.blog_id
            == current_blog.id,
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    data = update_data.model_dump(
        exclude_unset=True
    )

    # tag_idsはArticleの通常カラムではないので分離
    tag_ids = data.pop(
        "tag_ids",
        None,
    )

    # ------------------------------------
    # AffiliateProgramを変更する場合
    # 存在確認
    # ------------------------------------

    if "affiliate_program_id" in data:
        program = (
            db.query(AffiliateProgram)
            .filter(
                AffiliateProgram.id
                == data[
                    "affiliate_program_id"
                ],
                AffiliateProgram.blog_id
                == current_blog.id,
            )
            .first()
        )

        if program is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Affiliate program "
                    "not found"
                ),
            )

    # ------------------------------------
    # Categoryを変更する場合
    #
    # current_blogのCategoryだけ許可
    # ------------------------------------

    if (
        "category_id" in data
        and data["category_id"] is not None
    ):
        category = (
            db.query(Category)
            .filter(
                Category.id
                == data["category_id"],
                Category.blog_id
                == current_blog.id,
            )
            .first()
        )

        if category is None:
            raise HTTPException(
                status_code=404,
                detail="Category not found",
            )

    # ------------------------------------
    # Tagを変更する場合
    #
    # current_blogのTagだけ許可
    # ------------------------------------

    tags = None

    if tag_ids is not None:
        unique_tag_ids = list(
            dict.fromkeys(
                tag_ids
            )
        )

        if unique_tag_ids:
            tags = (
                db.query(Tag)
                .filter(
                    Tag.id.in_(
                        unique_tag_ids
                    ),
                    Tag.blog_id
                    == current_blog.id,
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

        else:
            # tag_ids=[] なら全Tag解除
            tags = []

    # ------------------------------------
    # slugを変更する場合は重複確認
    #
    # Article.slugはglobal UNIQUEなので
    # Blogを跨いで確認する。
    # ------------------------------------

    if "slug" in data:
        existing_slug = (
            db.query(Article)
            .filter(
                Article.slug
                == data["slug"],
                Article.id
                != article_id,
            )
            .first()
        )

        if existing_slug is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Article slug "
                    "already exists"
                ),
            )

    # ------------------------------------
    # Enum → DB保存用文字列
    # ------------------------------------

    if (
        "status" in data
        and data["status"] is not None
    ):
        data["status"] = (
            data["status"].value
        )

    # ------------------------------------
    # Article通常カラムを更新
    # ------------------------------------

    for field, value in data.items():
        setattr(
            article,
            field,
            value,
        )

    # ------------------------------------
    # Many-to-Many Tag更新
    # ------------------------------------

    if tags is not None:
        article.tags = tags

    try:
        db.commit()
        db.refresh(article)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Article conflicts "
                "with existing data"
            ),
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to update article",
        )

    return article


# ========================================
# DELETE
# DELETE /articles/{article_id}
# ========================================

@router.delete(
    "/{article_id}",
    status_code=204,
)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
):
    current_blog = get_current_blog(
        db=db,
    )

    article = (
        db.query(Article)
        .filter(
            Article.id == article_id,
            Article.blog_id
            == current_blog.id,
        )
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    try:
        db.delete(article)
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Article is referenced "
                "by other data"
            ),
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to delete article",
        )
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.blog import Blog
from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
)


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ========================================
# CURRENT BLOG
# ========================================

def get_current_blog(
    db: Session,
) -> Blog:
    """
    現在操作対象となる有効なブログを取得する。

    現段階では有効なブログのうち
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
# CREATE
# POST /categories/
# ========================================

@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=201,
)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
):
    current_blog = get_current_blog(
        db=db,
    )

    db_category = Category(
        blog_id=current_blog.id,
        name=category.name,
        slug=category.slug,
        description=category.description,
    )

    try:
        db.add(db_category)
        db.commit()
        db.refresh(db_category)

        return db_category

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Category name or slug "
                "already exists in this blog"
            ),
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Database error",
        )


# ========================================
# LIST
# GET /categories/
# ========================================

@router.get(
    "/",
    response_model=CategoryListResponse,
)
def get_categories(
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

    try:
        query = (
            db.query(Category)
            .filter(
                Category.blog_id
                == current_blog.id
            )
        )

        total = query.count()

        categories = (
            query
            .order_by(
                Category.id.asc()
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "items": categories,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Database error",
        )


# ========================================
# GET BY ID
# GET /categories/{category_id}
# ========================================

@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
):
    current_blog = get_current_blog(
        db=db,
    )

    try:
        category = (
            db.query(Category)
            .filter(
                Category.id
                == category_id,
                Category.blog_id
                == current_blog.id,
            )
            .first()
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Database error",
        )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Category not found",
        )

    return category


# ========================================
# UPDATE
# PATCH /categories/{category_id}
# ========================================

@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
)
def update_category(
    category_id: int,
    update_data: CategoryUpdate,
    db: Session = Depends(get_db),
):
    current_blog = get_current_blog(
        db=db,
    )

    try:
        category = (
            db.query(Category)
            .filter(
                Category.id
                == category_id,
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

        data = update_data.model_dump(
            exclude_unset=True
        )

        # blog_id はAPI経由では変更しない。
        data.pop(
            "blog_id",
            None,
        )

        for field, value in data.items():
            setattr(
                category,
                field,
                value,
            )

        db.commit()
        db.refresh(category)

        return category

    except HTTPException:
        raise

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Category name or slug "
                "already exists in this blog"
            ),
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Database error",
        )


# ========================================
# DELETE
# DELETE /categories/{category_id}
# ========================================

@router.delete(
    "/{category_id}",
    status_code=204,
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
):
    current_blog = get_current_blog(
        db=db,
    )

    try:
        category = (
            db.query(Category)
            .filter(
                Category.id
                == category_id,
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

        db.delete(category)
        db.commit()

    except HTTPException:
        raise

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Category is currently in use"
            ),
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Database error",
        )
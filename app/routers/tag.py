from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.tag import Tag
from app.schemas.tag import (
    TagCreate,
    TagUpdate,
    TagResponse,
    TagListResponse,
)


router = APIRouter(
    prefix="/tags",
    tags=["Tags"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ========================================
# CREATE
# POST /tags/
# ========================================

@router.post(
    "/",
    response_model=TagResponse,
    status_code=201,
)
def create_tag(
    tag: TagCreate,
    db: Session = Depends(get_db),
):
    db_tag = Tag(
        name=tag.name,
        slug=tag.slug,
    )

    try:
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)

        return db_tag

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Tag name or slug already exists",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Database error",
        )


# ========================================
# LIST
# GET /tags/
# ========================================

@router.get(
    "/",
    response_model=TagListResponse,
)
def get_tags(
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
    try:
        query = db.query(Tag)

        total = query.count()

        tags = (
            query
            .order_by(Tag.id.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "items": tags,
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
# GET /tags/{tag_id}
# ========================================

@router.get(
    "/{tag_id}",
    response_model=TagResponse,
)
def get_tag(
    tag_id: int,
    db: Session = Depends(get_db),
):
    try:
        tag = (
            db.query(Tag)
            .filter(Tag.id == tag_id)
            .first()
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Database error",
        )

    if tag is None:
        raise HTTPException(
            status_code=404,
            detail="Tag not found",
        )

    return tag


# ========================================
# UPDATE
# PATCH /tags/{tag_id}
# ========================================

@router.patch(
    "/{tag_id}",
    response_model=TagResponse,
)
def update_tag(
    tag_id: int,
    update_data: TagUpdate,
    db: Session = Depends(get_db),
):
    try:
        tag = (
            db.query(Tag)
            .filter(Tag.id == tag_id)
            .first()
        )

        if tag is None:
            raise HTTPException(
                status_code=404,
                detail="Tag not found",
            )

        data = update_data.model_dump(
            exclude_unset=True
        )

        for field, value in data.items():
            setattr(
                tag,
                field,
                value,
            )

        db.commit()
        db.refresh(tag)

        return tag

    except HTTPException:
        raise

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Tag name or slug already exists",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Database error",
        )


# ========================================
# DELETE
# DELETE /tags/{tag_id}
# ========================================

@router.delete(
    "/{tag_id}",
    status_code=204,
)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
):
    try:
        tag = (
            db.query(Tag)
            .filter(Tag.id == tag_id)
            .first()
        )

        if tag is None:
            raise HTTPException(
                status_code=404,
                detail="Tag not found",
            )

        db.delete(tag)
        db.commit()

    except HTTPException:
        raise

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Tag is currently in use",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Database error",
        )
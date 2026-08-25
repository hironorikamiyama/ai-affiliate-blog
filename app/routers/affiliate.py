from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.affiliate import AffiliateProgram
from app.schemas.affiliate import (
    AffiliateProgramCreate,
    AffiliateProgramUpdate,
    AffiliateProgramResponse,
    AffiliateProgramListResponse,
    ProgramStatus,
    RewardType,
)

from app.services.article_embedding import (
    get_embedding_similar_articles,
)

router = APIRouter(
    prefix="/programs",
    tags=["Affiliate Programs"],
)


# ========================================
# CREATE
# POST /programs/
# ========================================

@router.post(
    "/",
    response_model=AffiliateProgramResponse,
)
def create_program(
    program: AffiliateProgramCreate,
    db: Session = Depends(get_db),
):
    db_program = AffiliateProgram(
        name=program.name,
        asp_name=program.asp_name,
        affiliate_url=str(program.affiliate_url),
        category=program.category,
        reward_amount=program.reward_amount,
        reward_type=program.reward_type,
        status=program.status,
        description=program.description,
    )

    try:
        db.add(db_program)
        db.commit()
        db.refresh(db_program)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Affiliate program conflicts with existing data",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to create affiliate program",
        )

    return db_program


# ========================================
# LIST
# GET /programs/
# ========================================

@router.get(
    "/",
    response_model=AffiliateProgramListResponse,
)
def get_programs(
    category: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    asp_name: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    status: ProgramStatus | None = None,
    reward_type: RewardType | None = None,
    min_reward_amount: float | None = Query(
        default=None,
        ge=0,
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
    query = db.query(AffiliateProgram)

    if category is not None:
        query = query.filter(
            AffiliateProgram.category == category
        )

    if asp_name is not None:
        query = query.filter(
            AffiliateProgram.asp_name == asp_name
        )

    if status is not None:
        query = query.filter(
            AffiliateProgram.status == status.value
        )

    if reward_type is not None:
        query = query.filter(
            AffiliateProgram.reward_type == reward_type.value
        )

    if min_reward_amount is not None:
        query = query.filter(
            AffiliateProgram.reward_amount
            >= min_reward_amount
        )

    total = query.count()

    programs = (
        query
        .order_by(AffiliateProgram.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "items": programs,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ========================================
# GET BY ID
# GET /programs/{program_id}
# ========================================

@router.get(
    "/{program_id}",
    response_model=AffiliateProgramResponse,
)
def get_program(
    program_id: int,
    db: Session = Depends(get_db),
):
    program = (
        db.query(AffiliateProgram)
        .filter(AffiliateProgram.id == program_id)
        .first()
    )

    if program is None:
        raise HTTPException(
            status_code=404,
            detail="Affiliate program not found",
        )

    return program


# ========================================
# UPDATE
# PATCH /programs/{program_id}
# ========================================

@router.patch(
    "/{program_id}",
    response_model=AffiliateProgramResponse,
)
def update_program(
    program_id: int,
    update_data: AffiliateProgramUpdate,
    db: Session = Depends(get_db),
):
    program = (
        db.query(AffiliateProgram)
        .filter(AffiliateProgram.id == program_id)
        .first()
    )

    if program is None:
        raise HTTPException(
            status_code=404,
            detail="Affiliate program not found",
        )

    data = update_data.model_dump(
        exclude_unset=True
    )

    if (
        "affiliate_url" in data
        and data["affiliate_url"] is not None
    ):
        data["affiliate_url"] = str(
            data["affiliate_url"]
        )

    for field, value in data.items():
        setattr(
            program,
            field,
            value,
        )

    try:
        db.commit()
        db.refresh(program)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Affiliate program conflicts with existing data",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to update affiliate program",
        )

    return program


# ========================================
# DELETE
# DELETE /programs/{program_id}
# ========================================

@router.delete(
    "/{program_id}",
    status_code=204,
)
def delete_program(
    program_id: int,
    db: Session = Depends(get_db),
):
    program = (
        db.query(AffiliateProgram)
        .filter(AffiliateProgram.id == program_id)
        .first()
    )

    if program is None:
        raise HTTPException(
            status_code=404,
            detail="Affiliate program not found",
        )

    try:
        db.delete(program)
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Affiliate program is referenced by other data",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to delete affiliate program",
        )
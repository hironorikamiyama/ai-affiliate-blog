from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.affiliate import AffiliateProgram


from app.schemas.affiliate import (
    AffiliateProgramCreate,
    AffiliateProgramUpdate,
    AffiliateProgramResponse,
    AffiliateProgramListResponse,
    ProgramStatus,
    RewardType,
)


router = APIRouter(
    prefix="/programs",
    tags=["Affiliate Programs"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=AffiliateProgramResponse)
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

    db.add(db_program)
    db.commit()
    db.refresh(db_program)

    return db_program

@router.get("/", response_model=AffiliateProgramListResponse)
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
            AffiliateProgram.reward_amount >= min_reward_amount
        )

    # ページネーション前の総件数
    total = query.count()

    # 実際に返すデータ
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

@router.get("/{program_id}", response_model=AffiliateProgramResponse)
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

    data = update_data.model_dump(exclude_unset=True)
    if "affiliate_url" in data and data["affiliate_url"] is not None:
        data["affiliate_url"] = str(data["affiliate_url"])

    for field, value in data.items():
        setattr(program, field, value)

    db.commit()
    db.refresh(program)

    return program

@router.delete("/{program_id}", status_code=204)
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

    db.delete(program)
    db.commit()
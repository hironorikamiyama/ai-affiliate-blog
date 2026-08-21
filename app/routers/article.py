from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.affiliate import AffiliateProgram
from app.models.article import Article
from app.schemas.article import (
    ArticleGenerateRequest,
    ArticleResponse,
)
from app.services.ai_writer import generate_article


router = APIRouter(
    prefix="/articles",
    tags=["Articles"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/generate",
    response_model=ArticleResponse,
)
def create_article(
    request: ArticleGenerateRequest,
    db: Session = Depends(get_db),
):
    program = (
        db.query(AffiliateProgram)
        .filter(
            AffiliateProgram.id
            == request.affiliate_program_id
        )
        .first()
    )

    if program is None:
        raise HTTPException(
            status_code=404,
            detail="Affiliate program not found",
        )

    generated = generate_article(
        program=program,
        keyword=request.keyword,
    )

    article = Article(
        affiliate_program_id=program.id,
        title=generated["title"],
        keyword=request.keyword,
        body=generated["body"],
        status="draft",
    )

    db.add(article)
    db.commit()
    db.refresh(article)

    return article
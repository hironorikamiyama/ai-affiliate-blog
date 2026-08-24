from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.article import Article
from app.models.article_image import ArticleImage
from app.schemas.article_image import (
    ArticleImageResponse,
    ArticleImageUpdate,
)


router = APIRouter(
    prefix="/articles",
    tags=["Article Images"],
)


UPLOAD_DIR = Path("uploads/articles")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{article_id}/images",
    response_model=ArticleImageResponse,
)
async def upload_article_image(
    article_id: int,
    file: UploadFile = File(...),
    alt_text: str | None = Form(default=None),
    caption: str | None = Form(default=None),
    position: int = Form(default=0),
    is_featured: bool = Form(default=False),
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(Article.id == article_id)
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Only JPEG, PNG, and WebP images are allowed",
        )

    file_data = await file.read()

    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image file is too large. Maximum size is 5MB",
        )

    extension = ALLOWED_CONTENT_TYPES[file.content_type]

    stored_filename = f"{uuid4().hex}{extension}"

    article_directory = UPLOAD_DIR / str(article_id)
    article_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = article_directory / stored_filename

    with open(file_path, "wb") as buffer:
        buffer.write(file_data)

    if is_featured:
        (
            db.query(ArticleImage)
            .filter(
                ArticleImage.article_id == article_id,
                ArticleImage.is_featured.is_(True),
            )
            .update(
                {
                    ArticleImage.is_featured: False
                },
                synchronize_session=False,
            )
        )

    db_image = ArticleImage(
        article_id=article_id,
        file_path=str(file_path),
        original_filename=file.filename or stored_filename,
        alt_text=alt_text,
        caption=caption,
        position=position,
        is_featured=is_featured,
    )

    db.add(db_image)
    db.commit()
    db.refresh(db_image)

    return db_image


@router.get(
    "/{article_id}/images",
    response_model=list[ArticleImageResponse],
)
def get_article_images(
    article_id: int,
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .filter(Article.id == article_id)
        .first()
    )

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="Article not found",
        )

    images = (
        db.query(ArticleImage)
        .filter(ArticleImage.article_id == article_id)
        .order_by(
            ArticleImage.position.asc(),
            ArticleImage.id.asc(),
        )
        .all()
    )

    return images


@router.patch(
    "/article-images/{image_id}",
    response_model=ArticleImageResponse,
)
def update_article_image(
    image_id: int,
    update_data: ArticleImageUpdate,
    db: Session = Depends(get_db),
):
    image = (
        db.query(ArticleImage)
        .filter(ArticleImage.id == image_id)
        .first()
    )

    if image is None:
        raise HTTPException(
            status_code=404,
            detail="Article image not found",
        )

    data = update_data.model_dump(exclude_unset=True)

    # 新しくアイキャッチに指定する場合、
    # 同じ記事の他画像をすべて解除する
    if data.get("is_featured") is True:
        (
            db.query(ArticleImage)
            .filter(
                ArticleImage.article_id == image.article_id,
                ArticleImage.id != image_id,
                ArticleImage.is_featured.is_(True),
            )
            .update(
                {
                    ArticleImage.is_featured: False
                },
                synchronize_session=False,
            )
        )

    for field, value in data.items():
        setattr(image, field, value)

    db.commit()
    db.refresh(image)

    return image


@router.delete(
    "/article-images/{image_id}",
    status_code=204,
)
def delete_article_image(
    image_id: int,
    db: Session = Depends(get_db),
):
    image = (
        db.query(ArticleImage)
        .filter(ArticleImage.id == image_id)
        .first()
    )

    if image is None:
        raise HTTPException(
            status_code=404,
            detail="Article image not found",
        )

    file_path = Path(image.file_path)

    db.delete(image)
    db.commit()

    if file_path.exists():
        file_path.unlink()
        
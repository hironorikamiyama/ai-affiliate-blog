from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArticleImageResponse(BaseModel):
    id: int
    article_id: int
    file_path: str
    image_url: str
    original_filename: str
    alt_text: str | None = None
    caption: str | None = None
    position: int
    is_featured: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleImageUpdate(BaseModel):
    alt_text: str | None = Field(default=None, max_length=500)
    caption: str | None = None
    position: int | None = Field(default=None, ge=0)
    is_featured: bool | None = None

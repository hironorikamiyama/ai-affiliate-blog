from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.article_image import ArticleImageResponse
from app.schemas.category import CategoryResponse
from app.schemas.tag import TagResponse


class ArticleStatus(str, Enum):
    draft = "draft"
    review = "review"
    ready = "ready"
    published = "published"
    archived = "archived"


class ArticleCreate(BaseModel):
    affiliate_program_id: int = Field(ge=1)

    # Categoryは未分類記事も許可
    category_id: int | None = Field(
        default=None,
        ge=1,
    )

    # Article ↔ Tag は多対多
    tag_ids: list[int] = Field(
        default_factory=list,
    )

    title: str = Field(
        min_length=1,
        max_length=300,
    )

    slug: str = Field(
        min_length=1,
        max_length=300,
    )

    keyword: str = Field(
        min_length=1,
        max_length=200,
    )

    meta_description: str | None = Field(
        default=None,
        max_length=500,
    )

    body: str = Field(
        min_length=1,
    )

    status: ArticleStatus = ArticleStatus.draft


class ArticleUpdate(BaseModel):
    affiliate_program_id: int | None = Field(
        default=None,
        ge=1,
    )

    # nullを送ればCategory解除も可能
    category_id: int | None = Field(
        default=None,
        ge=1,
    )

    # []を送ればTag全解除
    tag_ids: list[int] | None = None

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=300,
    )

    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=300,
    )

    keyword: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    meta_description: str | None = Field(
        default=None,
        max_length=500,
    )

    body: str | None = Field(
        default=None,
        min_length=1,
    )

    status: ArticleStatus | None = None


class ArticleResponse(BaseModel):
    id: int
    affiliate_program_id: int

    category_id: int | None

    title: str
    slug: str
    keyword: str
    meta_description: str | None
    body: str
    status: ArticleStatus

    created_at: datetime
    updated_at: datetime

    category: CategoryResponse | None = None

    tags: list[TagResponse] = Field(
        default_factory=list,
    )

    images: list[ArticleImageResponse] = Field(
        default_factory=list,
    )

    model_config = ConfigDict(
        from_attributes=True,
    )


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    limit: int
    offset: int


class SimilarArticleResponse(BaseModel):
    article_id: int
    title: str
    slug: str
    similarity: float
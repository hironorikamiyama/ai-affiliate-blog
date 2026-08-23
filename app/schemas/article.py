from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ArticleStatus(str, Enum):
    draft = "draft"
    review = "review"
    ready = "ready"
    published = "published"
    archived = "archived"


class ArticleCreate(BaseModel):
    affiliate_program_id: int = Field(
        ge=1,
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

    title: str
    slug: str
    keyword: str
    meta_description: str | None
    body: str
    status: ArticleStatus

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    limit: int
    offset: int
    
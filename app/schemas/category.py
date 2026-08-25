from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    slug: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    description: str | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]
    total: int
    limit: int
    offset: int
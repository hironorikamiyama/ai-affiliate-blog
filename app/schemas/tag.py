from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TagCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    slug: str = Field(
        min_length=1,
        max_length=100,
    )


class TagUpdate(BaseModel):
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


class TagResponse(BaseModel):
    id: int
    name: str
    slug: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class TagListResponse(BaseModel):
    items: list[TagResponse]
    total: int
    limit: int
    offset: int
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class RewardType(str, Enum):
    fixed = "fixed"
    percentage = "percentage"
    other = "other"


class ProgramStatus(str, Enum):
    active = "active"
    paused = "paused"
    ended = "ended"


class AffiliateProgramCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=200,
    )

    asp_name: str = Field(
        min_length=1,
        max_length=100,
    )

    affiliate_url: HttpUrl

    category: str = Field(
        min_length=1,
        max_length=100,
    )

    reward_amount: float | None = Field(
        default=None,
        ge=0,
    )

    reward_type: RewardType = RewardType.fixed

    status: ProgramStatus = ProgramStatus.active

    description: str | None = Field(
        default=None,
        max_length=2000,
    )


class AffiliateProgramUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    asp_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    affiliate_url: HttpUrl | None = None

    category: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    reward_amount: float | None = Field(
        default=None,
        ge=0,
    )

    reward_type: RewardType | None = None

    status: ProgramStatus | None = None

    description: str | None = Field(
        default=None,
        max_length=2000,
    )


class AffiliateProgramResponse(BaseModel):
    id: int

    name: str
    asp_name: str
    affiliate_url: HttpUrl
    category: str

    reward_amount: float | None
    reward_type: RewardType
    status: ProgramStatus
    description: str | None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

class AffiliateProgramListResponse(BaseModel):
    items: list[AffiliateProgramResponse]
    total: int
    limit: int
    offset: int


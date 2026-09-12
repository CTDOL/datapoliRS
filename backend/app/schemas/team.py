from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

VALID_ROLES = ("admin", "operador", "leitor")
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class TeamMemberResponse(BaseModel):
    id: UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamMemberCreate(BaseModel):
    email: str = Field(..., max_length=255, pattern=EMAIL_PATTERN)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(..., pattern="^(admin|operador|leitor)$")


class TeamMemberUpdate(BaseModel):
    role: Optional[str] = Field(None, pattern="^(admin|operador|leitor)$")
    is_active: Optional[bool] = None

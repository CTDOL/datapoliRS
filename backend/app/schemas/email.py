from pydantic import BaseModel, Field

from app.schemas.team import EMAIL_PATTERN


class EmailTesteRequest(BaseModel):
    destinatario: str = Field(..., max_length=255, pattern=EMAIL_PATTERN)

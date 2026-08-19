import uuid
from pydantic import BaseModel
from typing import Optional

class UserInDB(BaseModel):
    id: int
    email: str
    is_active: bool
    tenant_id: uuid.UUID

class TokenData(BaseModel):
    email: Optional[str] = None
    tenant_id: Optional[uuid.UUID] = None

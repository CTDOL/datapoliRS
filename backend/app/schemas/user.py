import uuid
from pydantic import BaseModel, Field
from typing import Optional

class UserInDB(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    tenant_id: uuid.UUID
    role: str

class TokenData(BaseModel):
    email: Optional[str] = None
    tenant_id: Optional[uuid.UUID] = None

class PasswordChangeRequest(BaseModel):
    senha_atual: str
    nova_senha: str = Field(..., min_length=8, max_length=128)

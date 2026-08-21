import uuid
import logging
from typing import AsyncGenerator
from fastapi import HTTPException, status, Depends
import asyncpg
from app.core.database import getDatabaseConnection
from app.core.redis_client import CacheService

logger = logging.getLogger("Dependencies")


async def getDbConnection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Injeta uma conexão ativa do pool assíncrono do PostgreSQL."""
    async for connection in getDatabaseConnection():
        yield connection


from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from app.services.auth_service import AuthService
from app.schemas.user import UserInDB, TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: asyncpg.Connection = Depends(getDbConnection)
) -> UserInDB:
    """
    FastAPI Dependency to authenticate the user, extract their tenant context,
    and verify they exist and are active in the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = AuthService.decode_access_token(token)
        email: str = payload.get("sub")
        tenant_id_str: str = payload.get("tenant_id")
        
        if email is None or tenant_id_str is None:
            raise credentials_exception
            
        tenant_id = uuid.UUID(tenant_id_str)
        token_data = TokenData(email=email, tenant_id=tenant_id)
    except (JWTError, ValueError):
        raise credentials_exception

    query = """
        SELECT id, email, is_active, tenant_id
        FROM tb_users
        WHERE email = $1 AND tenant_id = $2
    """

    row = await db.fetchrow(query, token_data.email, token_data.tenant_id)

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or tenant mismatch",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserInDB(**dict(row))

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

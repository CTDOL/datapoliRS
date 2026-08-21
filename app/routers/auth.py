from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import asyncpg
from app.services.auth_service import AuthService
from app.core.dependencies import getDbConnection
from datetime import timedelta

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciais Incorretas",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    row = await connection.fetchrow(
        "SELECT email, hashed_password, is_active, tenant_id FROM tb_users WHERE email = $1",
        form_data.username,
    )
    if row is None or not row["is_active"]:
        raise credentials_exception

    if not AuthService.verify_password(form_data.password, row["hashed_password"]):
        raise credentials_exception

    access_token = AuthService.create_access_token(
        data={"sub": row["email"], "tenant_id": str(row["tenant_id"])},
        expires_delta=timedelta(minutes=60)
    )
    return {"access_token": access_token, "token_type": "bearer"}

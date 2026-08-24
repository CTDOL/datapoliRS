from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
import asyncpg
from app.core.config import settings
from app.services.auth_service import AuthService
from app.core.dependencies import AUTH_COOKIE_NAME, get_current_user, getDbConnection
from app.core.rate_limit import RateLimiter
from app.schemas.user import UserInDB, PasswordChangeRequest
from datetime import timedelta

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciais Incorretas",
    headers={"WWW-Authenticate": "Bearer"},
)

ACCESS_TOKEN_MAX_AGE_SECONDS = 60 * 60


@router.post("/login", dependencies=[Depends(RateLimiter(times=5, seconds=60, configKey="login"))])
async def login(
    response: Response,
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
        expires_delta=timedelta(seconds=ACCESS_TOKEN_MAX_AGE_SECONDS)
    )
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=access_token,
        max_age=ACCESS_TOKEN_MAX_AGE_SECONDS,
        path="/",
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
    )
    return {"message": "Login efetuado com sucesso"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/")
    return {"message": "Logout efetuado com sucesso"}


@router.get("/me")
async def read_current_user(current_user: UserInDB = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "tenant_id": str(current_user.tenant_id),
        "role": current_user.role,
    }


@router.post("/trocar-senha", dependencies=[Depends(RateLimiter(times=5, seconds=60, configKey="trocar_senha"))])
async def trocar_senha(
    payload: PasswordChangeRequest,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    row = await connection.fetchrow(
        "SELECT hashed_password FROM tb_users WHERE id = $1", current_user.id
    )
    if row is None or not AuthService.verify_password(payload.senha_atual, row["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta."
        )

    newHashedPassword = AuthService.get_password_hash(payload.nova_senha)
    await connection.execute(
        "UPDATE tb_users SET hashed_password = $1 WHERE id = $2",
        newHashedPassword, current_user.id
    )
    return {"message": "Senha alterada com sucesso"}

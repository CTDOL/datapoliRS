from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
import asyncpg
from app.core.config import settings
from app.services.auth_service import AuthService
from app.core.dependencies import AUTH_COOKIE_NAME, get_current_user, getDbConnection
from app.core.rate_limit import RateLimiter
from app.services import observabilidade_service, preferencias_service
from app.repositories.user_repository import UserRepository
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
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    ip = request.client.host if request.client else None
    row = await UserRepository.getAuthByEmail(connection, form_data.username)
    if row is None or not row["is_active"] or not AuthService.verify_password(form_data.password, row["hashed_password"]):
        # Registra a falha sem dizer se o e-mail existe: o log guarda o e-mail tentado (ADR 040).
        await observabilidade_service.registrar(connection, "login_falha", form_data.username, None,
                                                "/api/v1/auth/login", ip, 401)
        raise credentials_exception

    await observabilidade_service.registrar(connection, "login_ok", row["email"], str(row["tenant_id"]),
                                            "/api/v1/auth/login", ip, 200)

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
async def read_current_user(
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    # nm_mandato vai para o cabeçalho da tela: o operador precisa ver em qual gabinete está.
    gabinete = await connection.fetchrow(
        "SELECT nm_mandato, cor_primaria, cor_secundaria, tp_tema FROM tb_tenants WHERE id_tenant = $1",
        current_user.tenant_id,
    )
    return {
        "email": current_user.email,
        "tenant_id": str(current_user.tenant_id),
        "role": current_user.role,
        "must_change_password": current_user.must_change_password,
        "nm_mandato": gabinete["nm_mandato"] if gabinete else None,
        "cor_primaria": gabinete["cor_primaria"] if gabinete else None,
        "cor_secundaria": gabinete["cor_secundaria"] if gabinete else None,
        "tp_tema": gabinete["tp_tema"] if gabinete else "escuro",
        "preferencias": (await preferencias_service.obter(connection, current_user.id)).model_dump(),
    }


@router.post("/trocar-senha", dependencies=[Depends(RateLimiter(times=5, seconds=60, configKey="trocar_senha"))])
async def trocar_senha(
    payload: PasswordChangeRequest,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    hashedAtual = await UserRepository.getHashedPasswordById(connection, current_user.id)
    if hashedAtual is None or not AuthService.verify_password(payload.senha_atual, hashedAtual):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta."
        )

    newHashedPassword = AuthService.get_password_hash(payload.nova_senha)
    await UserRepository.updatePassword(connection, current_user.id, newHashedPassword)
    return {"message": "Senha alterada com sucesso"}

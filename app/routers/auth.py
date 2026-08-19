from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.services.auth_service import AuthService
from datetime import timedelta
import uuid

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Mock credenciais para o MVP (Zero Trust Testing)
    if form_data.username == "operador@campanha.com.br" and form_data.password == "admin123":
        tenant_id = "11111111-2222-3333-4444-555555555555"
        access_token = AuthService.create_access_token(
            data={"sub": form_data.username, "tenant_id": tenant_id},
            expires_delta=timedelta(minutes=60)
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais Incorretas",
        headers={"WWW-Authenticate": "Bearer"},
    )

import pytest
from datetime import timedelta
from fastapi import HTTPException
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
import uuid

# 1. JWT Generation and validation
def test_create_and_decode_token():
    tenant_id = uuid.uuid4()
    data = {"sub": "operador@campanha.com.br", "tenant_id": tenant_id}
    token = AuthService.create_access_token(data=data, expires_delta=timedelta(minutes=15))
    
    # Verify token
    payload = AuthService.decode_access_token(token)
    assert payload["sub"] == "operador@campanha.com.br"
    assert payload["tenant_id"] == str(tenant_id)

def test_invalid_token_throws_401():
    with pytest.raises(HTTPException) as exc:
        AuthService.decode_access_token("invalid.token.here")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Could not validate credentials"

# 2. Rate Limiting and Tenant Isolation would typically be tested via TestClient
# But since the prompt requests demonstrating how we test logic:
@pytest.mark.asyncio
async def test_get_current_user_tenant_isolation():
    # Mocking a DB connection that returns None for a mismatched tenant
    class MockDB:
        async def fetchrow(self, query, email, tenant_id):
            # Simulate a failure (e.g. user exists but tenant doesn't match)
            return None
            
    tenant_id = uuid.uuid4()
    token = AuthService.create_access_token({"sub": "hacker@evil.com", "tenant_id": tenant_id})
    
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, db=MockDB())
        
    assert exc.value.status_code == 401
    assert exc.value.detail == "User not found or tenant mismatch"

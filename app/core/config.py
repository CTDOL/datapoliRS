import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Configurações da aplicação centralizadas e tipadas via Pydantic Settings."""
    
    # Informações da API
    API_TITLE: str = "datapoliRS - Inteligência Eleitoral & Gabinete Digital"
    API_VERSION: str = "2.0.0"
    API_DESCRIPTION: str = "Microsserviço analítico de dados eleitorais e gestão de gabinete com PostGIS e Redis."
    
    # Servidor HTTP
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    # PostgreSQL & PostGIS
    POSTGRES_USER: str = "datapoli_user"
    POSTGRES_PASSWORD: str = "datapoli_pass"
    POSTGRES_DB: str = "datapoli_db"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql://datapoli_user:datapoli_pass@postgres:5432/datapoli_db"
    
    # Redis Cache
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://redis:6379/0"
    CACHE_DEFAULT_TTL: int = 86400  # 24 Horas
    
    # TSE
    TSE_BASE_URL: str = "https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura"
    TSE_TIMEOUT_SECONDS: float = 10.0
    
    # Auth — sem valor padrão: obrigatório vir de variável de ambiente (.env)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Usuário administrador criado automaticamente no startup, se ainda não existir
    ADMIN_EMAIL: str = "operador@campanha.com.br"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_TENANT_ID: str = "11111111-2222-3333-4444-555555555555"

    # CORS - lista separada por vírgula das origens do frontend
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = AppSettings()

# app/core/config.py - JEITO NOVO/CORRIGIDO
from pydantic_settings import BaseSettings, SettingsConfigDict # Importe SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Microsserviço Externo - Validação e Notificação"
    API_V1_STR: str = "/api/v1"


    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()
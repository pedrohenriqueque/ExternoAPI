from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sistema de Controle de Bicicletário - Externo API"
    API_V1_STR: str = "/api/v1"

    # Você pode adicionar outras configurações globais aqui no futuro
    # Exemplo: EMAIL_PROVIDER_URL: str = "default_url"

    class Config:
        case_sensitive = True
        # Se você quiser usar um arquivo .env para carregar configurações,
        # descomente a linha abaixo e crie um arquivo .env na raiz do projeto.
        # Lembre-se de adicionar .env ao seu .gitignore!
        # env_file = ".env"
        # env_file_encoding = 'utf-8'

settings = Settings()
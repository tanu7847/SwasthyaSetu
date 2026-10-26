from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://127.0.0.1:27017"
    mongodb_db: str = "swasthyasetu"
    jwt_secret: str = "development-only-change-me"
    jwt_expire_minutes: int = 720
    groq_api_key: str = ""
    groq_chat_model: str = "llama-3.3-70b-versatile"
    groq_stt_model: str = "whisper-large-v3-turbo"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str 
    HUGGINGFACE_TOKEN: str
    LANGCHAIN_API_KEY: str

    class Config:
        env_file = str(Path(__file__).resolve().parent.parent.parent.parent.parent / ".env")
        case_sensitive = True

settings = Settings()

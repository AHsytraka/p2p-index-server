from pydantic_settings import BaseSettings
from app.core.upload_config import *

class Settings(BaseSettings):
  PROJECT_NAME: str = "default"
  DATABASE_URL: str = "sqlite:///app/db/p2p.db"

  class Config:
    env_file = ".env"
    
settings = Settings()
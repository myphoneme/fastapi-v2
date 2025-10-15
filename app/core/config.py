from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import Field  

class Settings(BaseSettings):
    db_host : str = Field(..., env="DB_HOST")
    db_port : int = Field(..., env="DB_PORT")
    db_user : str = Field(..., env="DB_USER")
    db_password : Optional[str] = Field("", env="DB_PASSWORD")
    db_name : str = Field(..., env="DB_NAME")
    algorithm : str = Field(..., env="ALGORITHM")
    access_token_expire_minutes : int = Field(..., env="ACCESS_TOKEN_EXPIRE_MINUTES")
    secret_key : str = Field(..., env="SECRET_KEY")
    fernet_key : str = Field(..., env="FERNET_KEY")
    internal_token : str = Field(..., env="INTERNAL_TOKEN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
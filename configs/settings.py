from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    MODEL_PATH: str = "./models/uhg_model.pth"
    GITHUB_OWNER: str
    GITHUB_REPO: str
    GITHUB_JSON_PATH: str
    GITHUB_BRANCH: str = "main"
    GITHUB_TOKEN: str

    OPENAI_API_KEY: Optional[str] = None

    THREAT_SCORE_THRESHOLD_SUSPICIOUS: float = 0.5
    THREAT_SCORE_THRESHOLD_MALICIOUS: float = 0.8

settings = Settings()

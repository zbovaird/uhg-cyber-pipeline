from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    MODEL_PATH: str = "./models/uhg_model.pth"
    
    # Source repository (read-only)
    SRC_GITHUB_OWNER: str
    SRC_GITHUB_REPO: str
    SRC_GITHUB_JSON_PATH: str
    SRC_GITHUB_BRANCH: str = "main"
    
    # Output repository (write-only)
    OUT_GITHUB_OWNER: str
    OUT_GITHUB_REPO: str
    OUT_GITHUB_JSON_PATH: str
    OUT_GITHUB_BRANCH: str = "main"
    OUT_CHANGES_LATEST: str = "Data/changes/latest.json"
    OUT_CHANGES_HISTORY_DIR: str = "Data/changes/history"
    OUT_STATE_INDEX: str = "Data/state/index.json"
    
    # Authentication
    GITHUB_TOKEN: str
    OPENAI_API_KEY: Optional[str] = None

    # Scoring thresholds
    THREAT_SCORE_THRESHOLD_SUSPICIOUS: float = 0.5
    THREAT_SCORE_THRESHOLD_MALICIOUS: float = 0.8

    # Backward compatibility (deprecated - use SRC_* variants)
    @property
    def GITHUB_OWNER(self) -> str:
        return self.SRC_GITHUB_OWNER
    
    @property
    def GITHUB_REPO(self) -> str:
        return self.SRC_GITHUB_REPO
    
    @property
    def GITHUB_JSON_PATH(self) -> str:
        return self.SRC_GITHUB_JSON_PATH
    
    @property
    def GITHUB_BRANCH(self) -> str:
        return self.SRC_GITHUB_BRANCH

settings = Settings()

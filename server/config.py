import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MIN_VDI: int
    MAX_VDI: int
    MIN_RUNNED_VDI: int
    BUFFER_RV: int
    BUFFER_SV: int
    UPDATE_PERIOD: int

    GUACA_HOST: str
    GUACA_USER: str
    GUACA_PASS: str

    PVE_HOST: str
    PVE_USER: str
    PVE_PASS: str
    PVE_TEMPLATE_ID: int
    PVE_VDI_PREFIX: int

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    )
    
settings = Settings()

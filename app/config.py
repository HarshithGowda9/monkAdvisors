from pydantic import Field, BaseModel, Extra
from pydantic_settings import BaseSettings

class SamcoSettings(BaseSettings):
    SAMCO_USER_ID : str = Field(..., env = 'SAMCO_USER_ID')
    SAMCO_PASSWORD : str = Field(..., env = 'SAMCO_PASSWORD')
    SAMCO_YOB : str = Field(..., env = 'SAMCO_YOB')
    SAMCO_LOGIN_API : str = Field(..., env = 'SAMCO_LOGIN_API')
    SAMCO_HISTORY_CANDLE_API : str = Field(..., env = 'SAMCO_HISTORY_CANDLE_API')
    SAMCO_INTRADAY_CANDLE_API : str = Field(..., env = 'SAMCO_INTRADAY_CANDLE_API')
    SAMCO_QUOTE_API : str = Field(..., env = 'SAMCO_QUOTE_API')

    class Config:
        env_file = '.env'
        extra = Extra.ignore

class TVSettings(BaseSettings):
    TV_USER_ID : str = Field(..., env = 'TV_USER_ID')
    TV_PASSWORD : str = Field(..., env = 'TV_PASSWORD')

    class Config:
        env_file = '.env'
        extra = Extra.ignore

def get_samco_settings():
    return SamcoSettings()

def get_tv_settings():
    return TVSettings()

from pydantic import Field, BaseModel, Extra
from pydantic_settings import BaseSettings

class postgresSettings(BaseSettings):
    POSTGRES_DB_NAME : str = Field(..., env = 'POSTGRES_DB_NAME')
    POSTGRES_USER : str = Field(..., env = 'POSTGRES_USER')
    POSTGRES_PORT : str = Field(..., env = 'POSTGRES_PORT')
    POSTGRES_PASSWORD : str = Field(..., env = 'POSTGRES_PASSWORD')
    POSTGRES_HOST : str = Field(..., env = 'POSTGRES_HOST')

    class Config:
        env_file = '.env'
        extra = Extra.ignore

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


class TradingViewSettings(BaseSettings):
    TRADINGVIEW_USERNAME: str = Field(..., env='TRADINGVIEW_USERNAME')
    TRADINGVIEW_PASSWORD: str = Field(..., env='TRADINGVIEW_PASSWORD')
    TRADINGVIEW_API_KEY: str = Field(..., env='TRADINGVIEW_API_KEY')
    TRADINGVIEW_LOGIN_API: str = Field(..., env='TRADINGVIEW_LOGIN_API')
    TRADINGVIEW_CHART_API: str = Field(..., env='TRADINGVIEW_CHART_API')
    TRADINGVIEW_MARKET_DATA_API: str = Field(..., env='TRADINGVIEW_MARKET_DATA_API')
    TRADINGVIEW_ORDER_API: str = Field(..., env='TRADINGVIEW_ORDER_API')

    class Config:
        env_file = '.env'
        extra = Extra.ignore


class TVSettings(BaseSettings):
    TV_USER_ID : str = Field(..., env = 'TV_USER_ID')
    TV_PASSWORD : str = Field(..., env = 'TV_PASSWORD')

    class Config:
        env_file = '.env'
        extra = Extra.ignore

class Paths(BaseSettings):
    STRATEGY_DATAFRAME_PATH : str = Field(..., env = 'STRATEGY_DATAFRAME_PATH')
    class Config:
        env_file = '.env'
        extra = Extra.ignore


def get_samco_settings():
    return SamcoSettings()

def get_trading_view_settings():
    return TradingViewSettings()

def get_tv_settings():
    return TVSettings()

def get_paths():
    return Paths()

def get_postgres_settings():
    return postgresSettings()

from config import get_samco_settings, get_trading_view_settings
from tradeAppLogin import SamcoSession, TradingViewSession
from interface import TradeAuthorization


def samco_session()->TradeAuthorization:
    '''Returns the Samco Session'''
    samco_settings = get_samco_settings()
    samco_body = dict(userId = samco_settings.SAMCO_USER_ID, 
                        password = samco_settings.SAMCO_PASSWORD,
                        yob = samco_settings.SAMCO_YOB)
    samco_session = SamcoSession(samco_body)
    return samco_session

def tradingview_session() -> TradeAuthorization:
    '''Returns the TradingView Session'''
    #tradingview_settings = get_trading_view_settings()
    #tradingview_body = dict(
        #username=tradingview_settings.TRADINGVIEW_USERNAME,
        #password=tradingview_settings.TRADINGVIEW_PASSWORD,
        #api_key=tradingview_settings.TRADINGVIEW_API_KEY)
    tradingview_session = TradingViewSession('NIFTY')
    return tradingview_session

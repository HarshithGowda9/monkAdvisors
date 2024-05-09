from config import get_samco_settings
from tradeAppLogin import SamcoSession
from interface import TradeAuthorization

def samco_session()->TradeAuthorization:
    '''Returns the Samco Session'''
    samco_settings = get_samco_settings()
    samco_body = dict(userId = samco_settings.SAMCO_USER_ID, 
                        password = samco_settings.SAMCO_PASSWORD,
                        yob = samco_settings.SAMCO_YOB)
    samco_session = SamcoSession(samco_body)
    return samco_session
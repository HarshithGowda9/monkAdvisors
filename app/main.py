import time
from tradeAppLogin import SamcoSession
from config import get_samco_settings
from tradeAppData import SamcoTradeDataExtraction
from sessions import samco_session
from utils import EarliestMonth
from strategy.shortGainStrategy import ShortGainStrategy, shotGainScanner

if __name__ == '__main__':
    # define the session
    samco_session = samco_session()

    # find the earliest_month
    earliest_month = EarliestMonth(samco_session)
    earliest_month = earliest_month.earliest_month

    # Initiate shortGainStrategy
    shot_gain_scanner = shotGainScanner(samco_session, earliest_month)
    shot_gain_scanner.strategy_scanner()
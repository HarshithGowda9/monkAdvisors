import time
import pandas as pd
from tradeAppLogin import SamcoSession, TradingViewSession
from config import get_samco_settings
from tradeAppData import SamcoTradeDataExtraction
from sessions import samco_session, tradingview_session
from utils import EarliestMonth
from strategy.shortGainStrategy import ShortGainStrategy, ShortGainScanner, ShortGainCalculation
from strategy.macdStrategy import MACDStrategy, get_tv_data


if __name__ == '__main__':
    # define the session
    #samco_session = samco_session()

    # find the earliest_month
    #earliest_month = EarliestMonth(samco_session)
    #earliest_month = earliest_month.earliest_month

    # Initiate ShortGainScanner
    #short_gain_scanner = ShortGainScanner(samco_session, earliest_month)
    # if short_gain_scanner.performed == False:
    #     short_gain_scanner.strategy_scanner()

    # Extract the symbol from top_upside and top_downside
    #short_gain_calculation = ShortGainCalculation(samco_session, short_gain_scanner, earliest_month)
    #upside, downside = short_gain_calculation.set_upside_and_downside_bool_flags()
    #print(upside)
    #print(downside)
    # Initiate ShortGainStrategy
    # shot_gain_strategy = ShortGainStrategy()

    # define the session
    trading_session, tv_data = get_tv_data(symbol='NSE:TCS')

    MACD_Strategy = MACDStrategy('NSE:TCS', trading_session, tv_data)
    MACD_Strategy.run_strategy()
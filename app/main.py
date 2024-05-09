import time
from tradeAppLogin import SamcoSession
from config import get_samco_settings
from tradeAppData import SamcoTradeDataExtraction
from sessions import samco_session
from strategy.shortGainStrategy import ShortGainStrategy, save_short_gain_dataframe, samco_short_gain_strategy_scanner

if __name__ == '__main__':    
    samco_session = samco_session()
    # samco_trade_data = SamcoTradeDataExtraction('INFY', samco_session)
    # sgs = ShortGainStrategy(samco_session, samco_trade_data)
    # print(sgs.scan_opporunity())
    data = samco_short_gain_strategy_scanner(samco_session)
    x, y = save_short_gain_dataframe(data)
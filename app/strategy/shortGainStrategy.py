import time
import os
import pandas as pd
from datetime import datetime
from typing import List
from interface import Strategy, TradeAuthorization, TradeDataExtracion
from pydantic import BaseModel, field_validator
from utils import download_fno_symbols
from sessions import samco_session
from tradeAppData import SamcoTradeDataExtraction


def samco_short_gain_strategy_scanner(session:TradeAuthorization):
    '''
    Function to be run everyday at 9:15am.
    This function takes time to run and speed is bound by the samco server limits.
    Multiprocessing can not be done unless using multiple accounts.

    '''
    data = []
    fno_symbols = download_fno_symbols()
    print(fno_symbols)

    for symbol in fno_symbols:
        time.sleep(4)
        samco_trade_data = SamcoTradeDataExtraction(symbol, session)
        response = samco_trade_data.get_quote()
        open_value = float(response['openValue'])
        previous_close = float(response['previousClose'])
        print('Symbol: ', symbol, 'openValue: ', open_value, 'prevClose: ',previous_close)
        diff = (previous_close - open_value) / previous_close
        data.append([symbol, open_value, previous_close, diff])

    return data

def save_short_gain_dataframe(data:List[List])->pd.DataFrame:

    temp_data = pd.DataFrame(data, columns=['symbol', 'openValue', 'previousClose', 'diff'])
    temp_data['rank'] = temp_data['diff'].rank()
    temp_data_sorted = temp_data.sort_values(by='rank', ascending=True)
    top_upside = temp_data_sorted.iloc[:5]
    top_downside = temp_data_sorted.iloc[-5:]
    print(top_upside)
    print(top_downside)
    print(os.path.dirname(os.getcwd()))
    temp_data_sorted.to_csv('results.csv')
    top_upside.to_csv('top_upside.csv')
    top_downside.to_csv('top_downside.csv')
    return top_upside, top_downside
        

class ShortGainStrategy(Strategy):

    def __init__(self,
                 trade_data:TradeDataExtracion,
                 session: TradeAuthorization = samco_session()
                 ):
        self.session = session
        self.symbol = None
        self.active = False
        self.trade_data = trade_data
        self.fno_symbols = download_fno_symbols() 
        # later this should be shrinked to only a few symbols depending on performance and 
        # number of trade opportunity

    def __find_top_gainers_and_loosers(self, value):
        future_symbol = self.trade_data.earliest_month

    def scan_opporunity(self):
        print(self.trade_data.extract_ltp())
        # for item in sym_list:
        #     count += 1
        #     print("Data of ",item," ",count," of ",len(sym_list))
        #     sym = str(item)  +"24MAYFUT"
        #     sym1=sym.upper()
        #     sym = item.replace("&","_").replace("-","_")
        #     temp,ltp = s_quote(sym1,token,exh="NFO")
        #     if temp['status']=='Success':
        #         op = float(temp['openValue'])
        #         pc = float(temp['previousClose'])
        #         print("OP :",op,"PC: ",pc)
        #         diff = (pc - op) / pc
        #         #print(sym,op,pc,diff)
        #         temp = (sym,op,pc,diff)
        #         data.append(temp)
        #     else:
        #         print(sym1," gave an Error : ",temp['statusMessage'])
        

    def entry_price(self):
        return super().entry_price()
    
    def exit_price(self):
        return super().exit_price()
    
    def success_probability(self):
        return super().success_probability()
    
    def recent_trades(self):
        return super().recent_trades()
    
    def ongoing_trades(self):
        return super().ongoing_trades()
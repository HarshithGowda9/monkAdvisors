import os
import time
import json
import pandas as pd
from datetime import datetime
from typing import List
from interface import Strategy, TradeAuthorization, TradeDataExtracion, Scanner
from pydantic import BaseModel, field_validator
from utils import download_fno_symbols
from sessions import samco_session
from config import get_paths
from tradeAppData import SamcoTradeDataExtraction

class shotGainScanner(Scanner):
    def __init__(self, 
                 session: TradeAuthorization,
                 earliest_month: str
                 ):
        self.session = session
        self.earliest_month = earliest_month
        self.performed = False
        self.data = []
        self.data_path = self._data_path()

    def _data_path(self):
        file_path = os.path.abspath(__file__)
        file_name = os.path.basename(file_path)
        paths = get_paths()
        data_path = os.path.join(paths.STRATEGY_DATAFRAME_PATH, file_name[:-3])
        return data_path
    
    def __check_data_existence(self):
        '''
        Check if any existing data is present.
        Return True, if data is present.
        '''
        folder_content = os.listdir(self.data_path)
        if len(folder_content) != 0:
            return True
        else:
            return False
        
    def __clean_data_path(self):
        if self.__check_data_existence():
            files = os.listdir(self.data_path)
            for file in files:
                file_path = os.path.join(self.data_path, file)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")

    def _data_scanner(self):
        '''
        This function takes time to run and speed is bound by the samco server limits.
        Multiprocessing can not be done unless using multiple accounts.
        '''
        fno_symbols = download_fno_symbols()

        for symbol in fno_symbols:
            time.sleep(0.1)
            symbol = f'{symbol}{datetime.now().strftime("%y")}{self.earliest_month}FUT'
            print(symbol)
            response = self.session.session.get_quote(symbol)
            response = json.loads(response)
            if response['status'] == 'Success':
                open_value = float(response['openValue'])
                previous_close = float(response['previousClose'])
                print('Symbol: ', symbol, 'openValue: ', open_value, 'prevClose: ',previous_close)
                diff = (previous_close - open_value) / previous_close
                self.data.append([symbol, open_value, previous_close, diff])
        return self.data

    def __short_gain_dataframe(self)->pd.DataFrame:
        self.data = self._data_scanner()
        temp_data = pd.DataFrame(self.data, columns=['symbol', 'openValue', 'previousClose', 'diff'])
        temp_data['rank'] = temp_data['diff'].rank()
        temp_data_sorted = temp_data.sort_values(by='rank', ascending=True)
        top_upside = temp_data_sorted.iloc[:5]
        top_downside = temp_data_sorted.iloc[-5:]
        return temp_data_sorted, top_upside, top_downside
    
    def __save_short_gain_dataframe(self)->pd.DataFrame:
        self.__clean_data_path()
        temp_data_sorted, top_upside, top_downside = self.__short_gain_dataframe()
        try:
            temp_data_sorted.to_csv(os.path.join(self.data_path, 'sorted_result.csv'))
            top_upside.to_csv(os.path.join(self.data_path, 'top_upside.csv'))
            top_downside.to_csv(os.path.join(self.data_path, 'top_downside.csv'))
        except Exception as e:
            print(f'Unable to save shotGainStrategy csv files in: {self.data_path}')
    
    def strategy_scanner(self):
        '''
        performs the scanning if not done.
        '''
        if self.performed == False:
            self.__save_short_gain_dataframe()
            self.performed = True
            
class ShortGainStrategy(Strategy):
    def __init__(self,
                 session: TradeAuthorization,
                 trade_data:TradeDataExtracion,
                 scanner: Scanner,
                 symbol: str
                 ):
        self.session = session
        self.trade_data = trade_data
        self.scanner = scanner
        self.symbol = symbol
        self.active = False 

    def scan_opporunity(self):
        if self.scanner.performed == False:
            print('Downloading upside and downside data.')
            self.scanner.strategy_scanner()

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
import os
import time
import json
import pandas as pd
from typing import List, Tuple
from datetime import datetime
from collections import defaultdict
from pydantic import BaseModel, field_validator
from utils import download_fno_symbols
from ta.volatility import BollingerBands as bb 
from sessions import samco_session
from config import get_paths
from tradeAppData import SamcoTradeDataExtraction
from interface import Strategy, TradeAuthorization, TradeDataExtracion, Scanner, Calculation

class ShortGainScanner(Scanner):
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
            response = self.session.session.get_quote(symbol, exchange=self.session.session.EXCHANGE_NFO)
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

class ShortGainCalculation(Calculation):
    def __init__(self,
                 session: TradeAuthorization,
                 scanner: Scanner,
                 earliest_month: str):
        self.earliest_month = earliest_month
        self.session = session
        self.scanner = scanner

    def __load_dataframe_files_from_data_path(self)->pd.DataFrame:
        self.data_path = self.scanner.data_path
        upside_df = pd.read_csv(os.path.join(self.data_path, 'top_upside.csv'))
        downside_df = pd.read_csv(os.path.join(self.data_path, 'top_downside.csv'))
        return upside_df, downside_df
    
    def __load_days_data_from_trade_data(self, symbol:str):
        trade_data = SamcoTradeDataExtraction(symbol, self.session, self.earliest_month)
        days_data = trade_data.extract_history()
        return days_data, trade_data
    
    def __load_mins_data_from_trade_data(self, symbol:str, interval:str):
        trade_data = SamcoTradeDataExtraction(symbol, self.session, self.earliest_month)
        mins_data = trade_data.extract_ohlc(interval)
        return mins_data, trade_data
    
    def __find_bolinger_bands(self, 
                              data:pd.DataFrame, 
                              window_size:int, 
                              band_width:int):
        days_data_bb = bb(data['close'], window = window_size, window_dev = band_width)
        return days_data_bb
    
    def __select_the_upper_and_lower_band(self, data:pd.DataFrame):
        bb_top = data.bollinger_hband().iloc[-1]
        bb_down = data.bollinger_lband().iloc[-1]
        return bb_top, bb_down
    
    def __bollinger_selection(self, symbol:str, window_size = 20)->Tuple:
        days_data, trade_data = self.__load_days_data_from_trade_data(symbol=symbol)
        if trade_data.days < window_size:
            raise ValueError(f'ohlc data have only {trade_data.days} days, window_size needs to be less than that.')
        else:
            days_data_bb = self.__find_bolinger_bands(data = days_data, window_size= 20, band_width=0.7)
            bb_top_std, bb_down_std = self.__select_the_upper_and_lower_band(days_data_bb)
            return bb_top_std, bb_down_std
        
    def __upside_symbols_bb_selection(self, symbol: str, mins_data:pd.DataFrame, target_time):
        bb_top_std, _ = self.__bollinger_selection(symbol, window_size = 50)
        target_row = mins_data[mins_data.index.time == target_time]
        open = target_row.iloc[-1]['open']
        close = target_row.iloc[-1]['close']

        if (bb_top_std < float(open)) and (float(close) > float(open)) :
            return True
        else:
            return False      

    def __downside_symbols_bb_selection(self, symbol: str, mins_data:pd.DataFrame, target_time):
        _, bb_down_std = self.__bollinger_selection(symbol, window_size = 20)
        target_row = mins_data[mins_data.index.time == target_time]
        open = target_row.iloc[-1]['open']
        close = target_row.iloc[-1]['close']

        if (float(open) < bb_down_std) and (float(close) < float(open)) :
            return True
        else:
            return False
        

    def set_upside_and_downside_bool_flags(self):
        upside_df, downside_df = self.__load_dataframe_files_from_data_path()

        if 'Unnamed: 0' in upside_df.columns:
            upside_df.drop('Unnamed: 0', axis=1, inplace=True)
        if 'Unnamed: 0' in downside_df.columns:
            downside_df.drop('Unnamed: 0', axis=1, inplace=True)

        upside_df.reset_index(drop = True, inplace = True)
        downside_df.reset_index(drop = True, inplace = True)

        upside_df['status'] = [False for _ in range(len(upside_df))]
        downside_df['status'] = [False for _ in range(len(downside_df))]

        upside_df_final = pd.DataFrame(columns=upside_df.columns)
        downside_df_final = pd.DataFrame(columns=downside_df.columns)

        target_time = pd.to_datetime("09:15:00").time()
        for up_symbol, down_symbol in zip(upside_df['symbol'], downside_df['symbol']):
            mins_data_up, _ = self.__load_mins_data_from_trade_data(symbol=up_symbol, interval='15')
            mins_data_down, _ = self.__load_mins_data_from_trade_data(symbol=down_symbol, interval= '15')
            
            if self.__upside_symbols_bb_selection(up_symbol, mins_data_up, target_time):
                upside_df.loc[upside_df['symbol'] == up_symbol, 'status'] = True
                upside_data = upside_df[upside_df['symbol'] == up_symbol]
                upside_df_final = pd.concat([upside_df_final, upside_data], ignore_index=True)
            # else:
            #     upside_data = upside_df[upside_df['symbol'] == up_symbol]
            #     downside_df_final = pd.concat([downside_df_final, upside_data], ignore_index=True)

            if self.__downside_symbols_bb_selection(down_symbol, mins_data_down, target_time):
                downside_df.loc[downside_df['symbol'] == down_symbol, 'status'] = True
                downside_data = downside_df[downside_df['symbol'] == down_symbol]
                downside_df_final = pd.concat([downside_df_final, downside_data], ignore_index=True)
            # else:
            #     downside_data = downside_df[downside_df['symbol'] == down_symbol]
            #     upside_df_final = pd.concat([upside_df_final, downside_data], ignore_index=True)

        return upside_df_final, downside_df_final
    
    def pe_ce_indicators(self):
        return super().pe_ce_indicators()
            
class ShortGainStrategy(Strategy):
    def __init__(self,
                 session: TradeAuthorization,
                 trade_data:TradeDataExtracion,
                 scanner: Scanner,
                 earliest_month: str
                 ):
        self.session = session
        self.trade_data = trade_data
        self.scanner = scanner
        self.symbol = self.trade_data.symbol
        self.earliest_month = earliest_month
        self.active = False 

    def scan_opporunity(self):
        if self.scanner.performed == False:
            print('Scanner not initiated. Initiating it now.')
            print('Downloading upside and downside data.')
            print('It may take some time..')
            self.scanner.strategy_scanner()
            print('Scanning Done!')

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
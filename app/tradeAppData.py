'''
Trading App Data if a data extraction and Order API class.
The API can place order..
'''
import time
import json
import datetime
import pandas as pd
from typing import Dict, List, Tuple, Optional
from urllib.error import HTTPError
from tradeAppLogin import SamcoSession
from config import get_samco_settings
from error import RequestError, TradeAuthenticationFailedError, StrikePriceIntervalError
from utils import find_earliest_month
from sessions import samco_session
from interface import TradeDataExtracion, TradeAuthorization

class SamcoTradeDataExtraction(TradeDataExtracion):
    def __init__(self,
                 symbol: str,
                 session: TradeAuthorization, 
                 days: int = 4
                 ):
        self.samco = session
        self.symbol = symbol
        self.days = days
        self.today = datetime.datetime.now()
        self.from_date = self.today - datetime.timedelta(days=self.days)
        self.today = self.today.strftime("%Y-%m-%d %H:%M:%S")
        self.from_date = self.from_date.strftime("%Y-%m-%d %H:%M:%S")
        self.equity_derivatives_df = self.__extract_equity_derivatives_df()
        self.earliest_month = self.__extract_earliest_month_for_futures_contract()
        self.interval = None

    def __extract_equity_derivatives_df(self)->pd.DataFrame:
        if self.samco.is_authenticated() == True:
            response = self.samco.session.search_equity_derivative(search_symbol_name=self.symbol,
                                                                         exchange=self.samco.session.EXCHANGE_NFO)
            response = json.loads(response)
            if response['status'] == 'Success':
                equity_derivatives = response['searchResults']
                equity_derivatives_df = pd.DataFrame(equity_derivatives)
                return equity_derivatives_df
            else:
                raise RequestError(message=f'Request not succeed. Returned {response.status}')
        else:
            raise TradeAuthenticationFailedError(message = f'Trade App Authorization failed for {self.samco.session}')
        
    def __extract_earliest_month_for_futures_contract(self)->Tuple[pd.DataFrame, str]:
        '''
        Filters the futures (FUTSTK) data. Extract the earliest month.
        '''
        futures_trading_symbols = self.equity_derivatives_df.loc[self.equity_derivatives_df.instrument == 'FUTSTK', 'tradingSymbol']
        print(futures_trading_symbols)
        futures_month_list = [str(ts)[len(self.symbol)+2:len(self.symbol)+5] for ts in futures_trading_symbols]
        earliest_month = find_earliest_month(futures_month_list)
        self.earliest_month = earliest_month
        if len(self.earliest_month) == 3:
            return earliest_month
        else: 
            raise ValueError('Legth of month should be 3. ex: MAY')
    
    def __extract_strike_prices(self)->Tuple[List[int], List[int]]:
        trading_symbols_ce = self.equity_derivatives_df.tradingSymbol.loc[self.equity_derivatives_df.tradingSymbol.str.contains(self.earliest_month) &
                                                                          self.equity_derivatives_df.tradingSymbol.str.contains('CE')].tolist()
        trading_symbols_pe = self.equity_derivatives_df.tradingSymbol.loc[self.equity_derivatives_df.tradingSymbol.str.contains(self.earliest_month) &
                                                                          self.equity_derivatives_df.tradingSymbol.str.contains('PE')].tolist()
        strike_prices_ce = sorted([int(symbol[len(self.symbol)+5:-2]) for symbol in trading_symbols_ce])
        strike_prices_pe = sorted([int(symbol[len(self.symbol)+5:-2]) for symbol in trading_symbols_pe])
        return strike_prices_pe, strike_prices_ce
    
    def __find_strike_price_interval(self)->None:
        if self.interval == None:
            strike_prices_pe, strike_prices_ce = self.__extract_strike_prices()
            if len(strike_prices_pe) > 2:
                interval = int(strike_prices_pe[int(len(strike_prices_pe)/2)]) - int(strike_prices_pe[int(len(strike_prices_pe)/2)+1])
                self.interval = abs(interval)
            else:
                raise StrikePriceIntervalError(message='strike price method failed as len of contracts are less that 2.')
        
    def extract_ltp(self)->int:
        '''
        This method will return the Last Traded Price from samco websocket.
        '''
        if self.samco.is_authenticated() == True:
            response = self.samco.session.get_quote(symbol_name=self.symbol)
            response = json.loads(response)
            if response['status'] == 'Success':
                return float(response['lastTradedPrice'])
            else:
                raise RequestError(message=f'Request not succeed. Returned {response.status}')   
        else:
            raise TradeAuthenticationFailedError(message = f'Trade App Authorization failed for {self.samco.session}')
        
    def __find_nearest_strike_price_to_ltp(self)->int:
        ltp = self.extract_ltp()
        nearest_strike_price = round(ltp / self.interval) * self.interval
        return nearest_strike_price

    def extract_trading_symbol(self):
        self.__find_strike_price_interval()
        nsp = self.__find_nearest_strike_price_to_ltp()
        trading_symbol = f'{self.symbol}{datetime.datetime.now().strftime("%y")}{self.earliest_month}{nsp}'
        return trading_symbol

    def extract_history(self):
        if self.samco.is_authenticated() == True:
            response = self.samco.session.get_historical_candle_data(symbol_name='INFY24MAY1440CE',
                                                                     exchange=self.samco.session.EXCHANGE_NFO, 
                                                                     from_date=datetime.datetime.strptime(
                                                                         self.from_date, "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d"),
                                                                     to_date=datetime.datetime.strptime(
                                                                         self.today, "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d"))
            try:
                response = json.loads(response)
            except json.decoder.JSONDecodeError as e:
                raise HTTPError(url='https://api.stocknote.com/history/candleData', code=429, msg="Too Many Requests", hdrs={}, fp=None)

            if response['status'] == 'Success':
                history_candle_data = response['historicalCandleData']
                history_candle_data_df = pd.DataFrame(history_candle_data)
                history_candle_data_df.date = pd.to_datetime(history_candle_data_df.date, format='%Y-%m-%d')
                return history_candle_data_df
            else:
                raise RequestError(message=f'Request not succeed. Returned {response.status}')
        else:
            raise TradeAuthenticationFailedError(message = f'Trade App Authorization failed for {self.samco.session}')
        
        
    def extract_ohlc(self):
        if self.samco.is_authenticated() == True:
            response = self.samco.session.get_intraday_candle_data(symbol_name=self.symbol,
                                                  exchange=self.samco.session.EXCHANGE_NSE, 
                                                  from_date=self.from_date,
                                                  to_date=self.today)
            try:
                response = json.loads(response)
            except json.decoder.JSONDecodeError as e:
                raise HTTPError(url='https://api.stocknote.com/intraday/candleData', code=429, msg="Too Many Requests", hdrs={}, fp=None)

            if response['status'] == 'Success':
                candle_data = response['intradayCandleData']
                candle_data_df = pd.DataFrame(candle_data)
                candle_data_df.dateTime = pd.to_datetime(candle_data_df.dateTime, format='%Y-%m-%d %H:%M:%S.%f')
                return candle_data_df
            else:
                raise RequestError(message=f'Request not succeed. Returned {response.status}')
            
        else:
            raise TradeAuthenticationFailedError(message = f'Trade App Authorization failed for {self.samco.session}')
        
    def get_quote(self):
        if self.samco.is_authenticated() == True:
            response = self.samco.session.get_quote(symbol_name=self.symbol)
            try:
                response = json.loads(response)
            except json.decoder.JSONDecodeError as e:
                raise HTTPError(url='https://api.stocknote.com/intraday/candleData', code=429, msg="Too Many Requests", hdrs={}, fp=None)

            if response['status'] == 'Success':
                return response
            else:
                raise RequestError(message=f'Request not succeed. Returned {response.status}')
        else:
            raise TradeAuthenticationFailedError(message = f'Trade App Authorization failed for {self.samco.session}')


if __name__ == '__main__':
    samco_session = samco_session()
    samco_trade = SamcoTradeDataExtraction(session=samco_session,
                                           symbol='INFY',
                                           days = 4)
    print(samco_session.is_authenticated())
    # print(samco_trade.extract_ohlc())
    # print(samco_trade.extract_trading_symbol())
    # print(samco_trade.get_quote())
    # print(samco_trade.extract_history())

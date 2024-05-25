'''
Trading App Data if a data extraction and Order API class.
The API can place order..
'''
import json
import time
import datetime
import pandas as pd
from typing import Dict, List, Tuple
from urllib.error import HTTPError
from error import RequestError, TradeAuthenticationFailedError, StrikePriceIntervalError
from utils import EarliestMonth
from sessions import samco_session
from interface import TradeDataExtracion, TradeAuthorization

class SamcoTradeDataExtraction(TradeDataExtracion):
    def __init__(self,
                 symbol: str,
                 session: TradeAuthorization,
                 earliest_month: str,
                 days: int = 100
                 ):
        self.samco = session
        self.symbol = symbol
        self.days = days
        self.earliest_month = earliest_month
        self.today = datetime.datetime.now()
        self.from_date = self.today - datetime.timedelta(days=self.days)
        self.today = self.today.strftime("%Y-%m-%d %H:%M:%S")
        self.from_date = self.from_date.strftime("%Y-%m-%d %H:%M:%S")
        self.interval = None

    def __extract_equity_derivatives_df(self)->pd.DataFrame:
        if self.samco.is_authenticated() == True:
            response = self.samco.session.search_equity_derivative(search_symbol_name=self.symbol,
                                                                         exchange=self.samco.session.EXCHANGE_NFO)
            if '429 Too Many Requests' in response:
                print('Response failed with Too Many request. Trying again to reconnect.')
                time.sleep(2)
                return self.__extract_equity_derivatives_df()
            else:
                response = json.loads(response)
                if response['status'] == 'Success': 
                    equity_derivatives = response['searchResults']
                    equity_derivatives_df = pd.DataFrame(equity_derivatives)
                    return equity_derivatives_df
                else:
                    raise RequestError(message=f'Request not succeed. Returned {response.status}')
        else:
            raise TradeAuthenticationFailedError(message = f'Trade App Authorization failed for {self.samco.session}')
    
    def __extract_strike_prices(self)->Tuple[List[int], List[int]]:
        self.equity_derivatives_df = self.__extract_equity_derivatives_df()
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
        '''
        Daily data extraction for given days.
        '''
        if self.samco.is_authenticated() == True:
            response = self.samco.session.get_historical_candle_data(symbol_name=self.symbol,
                                                                     exchange=self.samco.session.EXCHANGE_NFO, 
                                                                     from_date=datetime.datetime.strptime(
                                                                         self.from_date, "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d"),
                                                                     to_date=datetime.datetime.strptime(
                                                                         self.today, "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d"))
            if '429 Too Many Requests' in response:
                print('Response failed with Too Many request. Trying again to reconnect.')
                time.sleep(2)
                return self.extract_history()
            else:
                response = json.loads(response)
                if response['status'] == 'Success':
                    print('Success!')
                    history_candle_data = response['historicalCandleData']
                    history_candle_data_df = pd.DataFrame(history_candle_data)
                    history_candle_data_df.date = pd.to_datetime(history_candle_data_df.date, format='%Y-%m-%d')
                    return history_candle_data_df
                else:
                    raise RequestError(message=f'Request not succeed. Returned {response.status}')
        else:
            raise TradeAuthenticationFailedError(message = f'Trade App Authorization failed for {self.samco.session}')
        
    def extract_ohlc(self, interval:str = '1'):
        '''
        This method by default extract 1 min interval data.
        '''
        if self.samco.is_authenticated() == True:
            self.from_date_ohlc = datetime.datetime.now() - datetime.timedelta(days=5)
            self.from_date_ohlc = self.from_date_ohlc.strftime("%Y-%m-%d %H:%M:%S")
            response = self.samco.session.get_intraday_candle_data(symbol_name=self.symbol,
                                                  exchange=self.samco.session.EXCHANGE_NFO, 
                                                  from_date=self.from_date_ohlc,
                                                  to_date=self.today)
            if '429 Too Many Requests' in response:
                print('Response failed with Too Many request. Trying again to reconnect.')
                time.sleep(2)
                return self.extract_ohlc(interval)
            else:
                response = json.loads(response)
                if response['status'] == 'Success':
                    print('Success!')
                    candle_data = response['intradayCandleData']
                    candle_data_df = pd.DataFrame(candle_data)
                    candle_data_df.dateTime = pd.to_datetime(candle_data_df.dateTime, format='%Y-%m-%d %H:%M:%S.%f')
                    candle_data_df.set_index('dateTime', inplace=True)
                    ohlc_dict = {
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'last'
                    }
                    candle_data_df_agg = candle_data_df.resample(f'{interval}min').apply(ohlc_dict).dropna()
                    return candle_data_df_agg
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
    earliest_month = EarliestMonth(samco_session)
    earliest_month = earliest_month.earliest_month
    samco_trade = SamcoTradeDataExtraction('INFY', samco_session, earliest_month, days = 30)
    # print(samco_trade.extract_ohlc('15'))
    # print(samco_trade.extract_trading_symbol())
    print(samco_trade.get_quote())
    # print(samco_trade.extract_history())

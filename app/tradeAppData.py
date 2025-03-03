'''
Trading App Data if a data extraction and Order API class.
The API can place order..
'''
import json
import time
import datetime
import pandas as pd
import requests, pytz
from zipfile import ZipFile
from io import BytesIO
from typing import Dict, List, Tuple
from urllib.error import HTTPError
from error import RequestError, TradeAuthenticationFailedError, StrikePriceIntervalError
from utils import EarliestMonth, round_to_nearest_0_05, _find_nearest_expiry
from sessions import samco_session, tradingview_session
from interface import TradeDataExtracion, TradeAuthorization
from price_loaders.price_loaders.tradingview import load_asset_price


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


class TradingViewDataExtraction(TradeDataExtracion):
    def __init__(self, symbol: str, session: TradeAuthorization):
        self.symbol = symbol
        self.session = session
        self.NFO_list = self.NFO_list()
        self.timezone = pytz.timezone('Asia/Kolkata')
        self.ep = None
        self.dir = None
        self.timeframe = None

    
    def download_and_read_csv(self, url: str) -> pd.DataFrame:
        """
        Downloads a ZIP file from the given URL, extracts its contents,
        and reads the CSV file into a pandas DataFrame.

        Parameters:
        url (str): The URL of the ZIP file containing the CSV.

        Returns:
        pd.DataFrame: The extracted CSV data as a DataFrame, or None if an error occurs.
        """
        try:
            # Download the ZIP file
            response = requests.get(url)
            response.raise_for_status()  # Raise an HTTPError for bad responses

            # Extract the ZIP file content
            with ZipFile(BytesIO(response.content)) as zip_file:
                csv_files = zip_file.namelist()
                if not csv_files:
                    raise ValueError("No files found in the ZIP archive.")
                
                csv_filename = csv_files[0]  
                print(f"Extracting: {csv_filename}")
                
                with zip_file.open(csv_filename) as csv_file:
                    df = pd.read_csv(csv_file)
                    return df
        
        except requests.exceptions.RequestException as e:
            print(f"Download failed: {e}")
            df = None
        except ValueError as e:
            print(f"File extraction error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return None
        
    def NFO_list(self) -> pd.DataFrame:
            """ 
            Function downloads the NFO symbols list from the given URL and returns a DataFrame. 
            
            Parameters: None
            
            Returns: pd.Dataframe 
            """

            url = "https://go.mynt.in/NFO_symbols.txt.zip"
            df = self.download_and_read_csv(url)
            return df
    
    
    def calculate_entry_prices(self):
            """
            Computes entry prices and trade directions using MACD histogram crossovers.
            """
            # Define the timezone
            timezone = pytz.timezone("Asia/Kolkata")
            
            # Load asset price data
            symbol = self.symbol
            timeframe = '5'                    # 5 minute candles      
            price_data = load_asset_price(symbol, 200, timeframe, timezone)
            
            # Remove the last row (possibly incomplete data)
            price_data = price_data.iloc[:-1]
            
            # Compute MACD indicators
            price_data['fast_ema'] = price_data['close'].ewm(span=12, adjust=False).mean()
            price_data['slow_ema'] = price_data['close'].ewm(span=26, adjust=False).mean()
            price_data['macd_line'] = price_data['fast_ema'] - price_data['slow_ema']
            price_data['signal_line'] = price_data['macd_line'].ewm(span=9, adjust=False).mean()
            price_data['macd_histogram'] = price_data['macd_line'] - price_data['signal_line']
            
            # Initialize Entry Price and Trade Direction columns
            price_data['entry_price'] = pd.NA
            price_data['trade_direction'] = pd.NA
            
            # Iterate over the DataFrame to determine entry points
            for i in range(1, len(price_data)):
                # Retrieve histogram values for crossover detection
                prev_prev_hist = float(price_data['macd_histogram'].iloc[i-2]) if i >= 2 else None
                prev_hist = float(price_data['macd_histogram'].iloc[i-1])
                current_hist = float(price_data['macd_histogram'].iloc[i]) if i < len(price_data) else None
                
                # Get high and low prices for rounding purposes
                high_price = float(price_data['high'].iloc[i])
                low_price = float(price_data['low'].iloc[i])
                
                # Detect bullish crossover (Buy Signal)
                if prev_prev_hist is not None and current_hist is not None and prev_prev_hist > prev_hist < current_hist:
                    entry_price = round_to_nearest_0_05(high_price)
                    trade_direction = "Buy"
                
                # Detect bearish crossover (Sell Signal)
                elif prev_prev_hist is not None and current_hist is not None and prev_prev_hist < prev_hist > current_hist:
                    entry_price = round_to_nearest_0_05(low_price)
                    trade_direction = "Sell"
                
                # Maintain previous values if no crossover is detected
                else:
                    entry_price = price_data['entry_price'].iloc[i-1]
                    trade_direction = price_data['trade_direction'].iloc[i-1]
                
                # Update DataFrame with calculated values
                price_data.at[i, 'entry_price'] = entry_price
                price_data.at[i, 'trade_direction'] = trade_direction
            
            # Return the last entry price, direction and time
            self.ep = round(float(entry_price))
            self.dir = trade_direction
            self.timeframe = price_data['time'].iloc[-1]

            return self.ep, self.dir, self.timeframe



    def extract_ltp(self):
        data = load_asset_price(self.symbol, 1, "1D", self.timezone)
        ltp = float(data['close'].values[0])
        return(ltp)
        

    def extract_trading_symbol(self):
        pass

    def extract_ohlc(self):
        pass

    def extract_history(self):
        pass

    def get_quote(self):
        pass


if __name__ == '__main__':
    #samco_session = samco_session()
    #earliest_month = EarliestMonth(samco_session)
    #earliest_month = earliest_month.earliest_month
    #samco_trade = SamcoTradeDataExtraction('INFY', samco_session, earliest_month, days = 30)
    # print(samco_trade.extract_ohlc('15'))
    # print(samco_trade.extract_trading_symbol())
    #print(samco_trade.get_quote())
    # print(samco_trade.extract_history())

    trading_view_session = tradingview_session()
    nearest_expiry_date = _find_nearest_expiry()
    trading_view = TradingViewDataExtraction('', trading_view_session)
    print(trading_view.calculate_entry_prices())
    print(trading_view.extract_ltp())



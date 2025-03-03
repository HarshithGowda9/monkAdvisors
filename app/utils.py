import os
import json, random, time
import calendar
import datetime
import asyncio
import websockets
import numpy as np
from typing import Dict, List, Tuple
import pandas as pd
#import nsepython as nse
from interface import TradeAuthorization, Session
from error import TradeAuthenticationFailedError, RequestError
from telegram import Bot


def find_earliest_month(months: List[str]) -> str:
    month_abbr = [calendar.month_abbr[i].lower() for i in range(1, 13)]
    earliest_month_abbr = min(months, key=lambda x: month_abbr.index(x.lower()))
    earliest_month_index = month_abbr.index(earliest_month_abbr.lower())
    earliest_month_name = calendar.month_name[earliest_month_index + 1]
    return earliest_month_name.upper()

class EarliestMonth:
    '''
    This class will help to calculate the earliest month.
    Earlies month is required to generate TradeSymbol.
    
    '''
    def __init__(self, session: TradeAuthorization):
        self.symbol = 'INFY'
        self.session = session
        self.equity_derivatives_df = self.__extract_equity_derivatives_df()
        self.earliest_month = self.__extract_earliest_month_for_futures_contract()

    def __extract_equity_derivatives_df(self)->pd.DataFrame:
        if self.session.is_authenticated() == True:
            response = self.session.session.search_equity_derivative(search_symbol_name=self.symbol,
                                                                         exchange=self.session.session.EXCHANGE_NFO)
            response = json.loads(response)
            if response['status'] == 'Success':
                equity_derivatives = response['searchResults']
                equity_derivatives_df = pd.DataFrame(equity_derivatives)
                return equity_derivatives_df
            else:
                raise RequestError(message=f'Request not succeed. Returned {response.status}')
        else:
            raise TradeAuthenticationFailedError(message = f'Trade App Authorization failed for {self.session.session}')
        
    def __extract_earliest_month_for_futures_contract(self)->Tuple[pd.DataFrame, str]:
        '''
        Filters the futures (FUTSTK) data. Extract the earliest month.
        '''
        futures_trading_symbols = self.equity_derivatives_df.loc[self.equity_derivatives_df.instrument == 'FUTSTK', 'tradingSymbol']
        current_year = str(datetime.datetime.now().strftime("%y"))
        futures_month_list = [ts.split(current_year)[1][:3] for ts in futures_trading_symbols]
        earliest_month = find_earliest_month(futures_month_list)
        self.earliest_month = earliest_month
        if len(self.earliest_month) == 3:
            return earliest_month
        else: 
            raise ValueError('Legth of month should be 3. ex: MAY')

def download_fno_symbols()->List[str]:
    '''
    Returns the list of symbols for available trade.
    Note: {'NIFTY', 'NIFTYIT', 'BANKNIFTY'} are removed from symbols.
    '''
    fno = nse.fnolist()
    del_set = {'NIFTY', 'NIFTYIT', 'BANKNIFTY'}
    data = set(fno) - del_set
    return list(data)

def round_to_nearest_0_05(number):
    rounded_number = round(number, 2)
    adjusted_number = round(rounded_number / 0.05) * 0.05
    return adjusted_number

def _find_nearest_expiry(self, data: pd.DataFrame, symbol: str, instrument: str, option_type: str, strike_price: float) -> str:
    """
    Finds the nearest expiry date for a given options contract based on specific conditions.

    Args:
        data (pd.DataFrame): The dataset containing options contract details.
        symbol (str): The symbol of the options contract.
        instrument (str): The type of instrument (e.g., OPTSTK, OPTIDX).
        option_type (str): The option type (e.g., CALL, PUT).
        strike_price (float): The strike price of the contract.

    Returns:
        str: The nearest expiry date in 'DD-MMM-YYYY' format.

    Raises:
        ValueError: If no expiry dates are found or if the filtered data is empty.
    """
    # Filter the data based on the provided conditions
    filtered_data = data[
        (data["Symbol"] == symbol) &
        (data["Instrument"] == instrument) &
        (data["OptionType"] == option_type) &
        (data["StrikePrice"] == strike_price)
    ]

    # Ensure the filtered data is not empty
    if filtered_data.empty:
        raise ValueError(f"No data found for the specified conditions: {symbol}, {instrument}, {option_type}, {strike_price}")

    # Extract and sort expiry dates
    expiry_dates = filtered_data["Expiry"].tolist()
    date_format = "%d-%b-%Y"
    try:
        parsed_dates = [datetime.strptime(date, date_format) for date in expiry_dates]
    except ValueError as e:
        raise ValueError(f"Error parsing expiry dates: {e}")

    parsed_dates.sort()

    # Get the nearest expiry date
    nearest_expiry = parsed_dates[0]
    return nearest_expiry.strftime(date_format).upper()


def get_strike_price(df, sym, ltp):
    # Filter the DataFrame
    filtered_df = df[(df['exchange'] == 'NFO') & 
                     (df['instrument'] == 'OPTSTK') & 
                     (df['name'] == sym)]
    
    # Check if the filtered DataFrame is not empty
    if not filtered_df.empty:
        # Calculate the absolute difference between strikePrice and LTP
        filtered_df['diff'] = np.abs(filtered_df['strikePrice'] - ltp)
        
        # Get the index of the row with the minimum difference
        min_diff_index = filtered_df['diff'].idxmin()
        
        # Return the strikePrice of the row with the minimum difference
        return filtered_df.loc[min_diff_index, 'strikePrice']
    else:
        return None



def generate_random_token(length=12):
    """Generates a random token of the given length."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return ''.join(random.choice(chars) for _ in range(length))

def current_epoch_time():
    """Returns the current epoch time."""
    return int(time.time())

async def telegam_msg(msg):

    # Telegram Configuration

    TELEGRAM_BOT_TOKEN = '6826962569:AAEVHzPQnNXNuBB0mGcCiaDzLMARvk79Cpc'
    TELEGRAM_CHAT_ID = '-1002138820012'
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)


def send_telegram_message(msg):
    asyncio.run(telegam_msg(msg))



#if __name__ == '__main__':
#    fno_data = download_fno_symbols()
#    print(fno_data)
import os
import json
import calendar
import datetime
from typing import Dict, List, Tuple
import pandas as pd
import nsepython as nse
from interface import TradeAuthorization
from error import TradeAuthenticationFailedError, RequestError

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

if __name__ == '__main__':
    fno_data = download_fno_symbols()
    print(fno_data)
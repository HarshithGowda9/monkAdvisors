import os
import calendar
from typing import Dict, List
import pandas as pd
import nsepython as nse

def find_earliest_month(months: List[str]) -> str:
    month_abbr = [calendar.month_abbr[i].lower() for i in range(1, 13)]
    earliest_month_abbr = min(months, key=lambda x: month_abbr.index(x.lower()))
    earliest_month_index = month_abbr.index(earliest_month_abbr.lower())
    earliest_month_name = calendar.month_name[earliest_month_index + 1]
    return earliest_month_name.upper()

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
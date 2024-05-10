from abc import ABC, abstractmethod

#-----TRADING APP RELATED INTERFACES------#

class TradeAuthorization(ABC):
    '''Authorization for trade Applications. '''
    @abstractmethod
    def is_authenticated(self):
        pass

class Session(TradeAuthorization):
    '''Generic session creator.'''
    def __init__(self):
        self.verified = False
        self.Token = None
    @abstractmethod
    def _login(self):
        pass
    @abstractmethod
    def _activate_session(self):
        pass
    @abstractmethod
    def is_authenticated(self):
        pass
class TradeDataExtracion(ABC):
    @abstractmethod
    def extract_trading_symbol(self):
        '''
        Extract trading symbols.
        '''
        pass

    @abstractmethod
    def extract_ltp(self):
        '''
        Extract ltp.
        '''
        pass
    
    @abstractmethod
    def extract_ohlc(self):
        '''
        Extract Open, High, Low and Close data. 
        Mostly extract 1min data.
        '''
        pass
    @abstractmethod
    def extract_history(self):
        '''
        Get history candle data from specific date upto today (default).
        Extract date wise data.
        '''
        pass
    @abstractmethod
    def get_quote(self):
        '''
        Return openPrice, PrevClose and ListingId.
        '''
        pass

# STRATEGY INTERFACE

class Scanner(ABC):
    '''
    Support class to Strategy.scan_opportunity() method.
    Class to be run everyday at 9:15am.
    '''
    @abstractmethod
    def strategy_scanner(self):
        pass

class Strategy(ABC):

    @abstractmethod
    def scan_opporunity(self):
        pass

    @abstractmethod
    def entry_price(self):
        '''
        Returns the entry price for trade.
        '''
        pass
    @abstractmethod
    def exit_price(self):
        '''
        Returns the exit price for trade.
        '''
        pass
    @abstractmethod
    def success_probability(self):
        '''
        Overall success rate of the strategy for given symbol for different factors.
        '''
        pass
    @abstractmethod
    def recent_trades(self):
        '''
        History of recent trades extracted from database for different users.
        '''
        pass
    @abstractmethod
    def ongoing_trades(self):
        '''
        How many symbols are using the strategy.
        '''
        pass

# ---- TRADE ----- #

class TradeOpportunity(ABC):
    @abstractmethod
    def strategy_opportunity(self):
        pass
    @abstractmethod
    def success_probability(self):
        pass

class TradeSetup(ABC):
    @abstractmethod
    def set_strategy(self):
        pass
    @abstractmethod
    def set_profit_margin_stop_loss(self):
        pass
    @abstractmethod
    def set_trade_application(self):
        pass
    @abstractmethod
    def set_trade_amount(self):
        pass

class Trade(ABC):
    @abstractmethod
    def place_order(self):
        pass
    @abstractmethod
    def update_profit_and_loss(self):
        pass
    @abstractmethod
    def update_transaction(self):
        pass
    @abstractmethod
    def update_strategy_performance(self):
        pass
    @abstractmethod
    def update_user_performance(self):
        pass
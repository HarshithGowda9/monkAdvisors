from pydantic import BaseModel, ValidationError, validators

class RequestError(Exception):
    '''Custom error when http request to server fails.'''
    def __init__(self, message: str)->None:
        self.message = message
        super().__init__()

class TradeAuthenticationFailedError(Exception):
    '''Custom error when Authentication for fails for Trade API.'''
    def __init__(self, message: str)->None:
        self.message = message
        super().__init__()

class StrikePriceIntervalError(Exception):
    '''Custom error when strike price is not extracted.'''
    def __init__(self, message: str)->None:
        self.message = message
        super().__init__()
'''
This is only for Trading App registration.
A trading App is primarily use for placing the order.
If you are trying to login to any other application like TradingView
use utils.py instead.
'''
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge
from config import get_samco_settings
from interface import Session

class SamcoSession(Session):
    '''Samco Session.'''
    def __init__(self, body):
        super().__init__()
        self.body = body
        self.response = None
        self.session = StocknoteAPIPythonBridge()
        self._activate_session()

    def __repr__(self):
        return json.dumps(self.response)
    
    def __str__(self):
        return json.dumps(self.response)

    def _login(self):
        try:
            login_response = self.session.login(body = self.body)
            # login_response is a json string
            login_response = json.loads(login_response) # convert back to json
            if 'sessionToken' in login_response:
                return login_response
            else:
                print('Login Failed.', login_response)
        except Exception as e: 
            print(f'Login Failed for {e}. Retrying Login in 20 secs....')
            time.sleep(20)
            self._login()

    def _activate_session(self)->Tuple:
        '''
        This method activates the Samco Session. 
        Returns: A tuple -> (samco object, token string) '''
        response = self._login()
        if response:
            self.verified = True
            self.Token = response.get('sessionToken')  # Safely extract session token
            self.session.set_session_token(self.Token)
            self.response = response
        else:
            return None
        
    def is_authenticated(self):
        return self.verified
        

# class ZerodhaSession(Session):
#     pass

if __name__ == '__main__':
    samco_settings = get_samco_settings()
    samco_body = dict(userId = samco_settings.SAMCO_USER_ID, 
                      password = samco_settings.SAMCO_PASSWORD,
                      yob = samco_settings.SAMCO_YOB)
    samco = SamcoSession(samco_body)
    print(samco.is_authenticated())
    
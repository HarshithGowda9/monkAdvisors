'''
This is only for Trading App registration.
A trading App is primarily use for placing the order.
If you are trying to login to any other application like TradingView
use utils.py instead.
'''
from random import choices
import string
import time
import json
import re
from datetime import datetime
import asyncio, sqlite3
import websockets
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
#from snapi_py_client.snapi_bridge import StocknoteAPIPythonBridge
from config import get_samco_settings
from interface import Session
from utils import current_epoch_time, generate_random_token
from collections import deque
import signal, sys



class SamcoSession(Session):
    '''Samco Session.'''
    def __init__(self, body):
        super().__init__()
        self.body = body
        self.response = None
        #self.session = StocknoteAPIPythonBridge()
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
        

class TradingViewSession:
    def __init__(self, symbols, verbose=False, save=False):
        if isinstance(symbols, str):
            self.symbols = [symbols]
        self.verbose = verbose
        self.save = save
        self.states = {}
        for symbol in self.symbols:
            self.states[symbol] = {"volume": 0, "price": 0, "change": 0, "changePercentage": 0, "time": 0}
        self.saves = 0
        self.loop = asyncio.get_event_loop()
        self.run = True
        self.connected = False
        self.connection = None
        signal.signal(signal.SIGINT, self.cleanup_on_exit)   # Handle Ctrl+C
        signal.signal(signal.SIGTERM, self.cleanup_on_exit)  # Handle termination signals

    # Generate random token
    def createRandomToken(self, length=12):
        return ''.join(choices(string.ascii_letters + string.digits, k=length))

    # Convert message string to object
    async def readMessage(self, message):
        messages = message.split("~m~")
        messagesObj = []
        for message in messages:
            if '{' in message or '[' in message:
                messagesObj.append(json.loads(message))
            else:
                if "~h~" in message:
                    await self.connection.send(f"~m~{len(message)}~m~{message}")
        return messagesObj

    # Convert object to message string
    def createMessage(self, name, params):
        message = json.dumps({'m': name, 'p': params})
        return f"~m~{len(message)}~m~{message}"

    # Send message
    async def sendMessage(self, name, params):
        message = self.createMessage(name, params)
        #print(f"Sending message: {message}")
        await self.connection.send(message)

    # Authenticate session and subscribe to price updates
    async def authenticate(self):
        self.cs = "cs_" + self.createRandomToken()

        await self.sendMessage("set_auth_token", ["unauthorized_user_token"])
        #print(" Authentication token sent.")

        await self.sendMessage("chart_create_session", [self.cs, ""])
        #print(f" Chart session created: {self.cs}")

        q = self.createRandomToken()
        qs = "qs_" + q
        qsl = "qs_snapshoter_basic-symbol-quotes_" + q

        await self.sendMessage("quote_create_session", [qs])
        #print(f" Quote session created: {qs}")

        await self.sendMessage("quote_create_session", [qsl])
        #print(f" Quote snapshoter session created: {qsl}")

        await self.sendMessage(
            "quote_set_fields",
            [
                qsl, "base-currency-logoid", "ch", "chp", "currency-logoid", "currency_code",
                "currency_id", "base_currency_id", "current_session", "description", "exchange",
                "format", "fractional", "is_tradable", "language", "local_description",
                "listed_exchange", "logoid", "lp", "lp_time", "minmov", "minmove2",
                "original_name", "pricescale", "pro_name", "short_name", "type", "typespecs",
                "update_mode", "volume", "variable_tick_size", "value_unit_id"
            ]
        )
        #print(f" Set quote fields.")

        #print(f"Subscribing to symbols: {self.symbols}")

        await self.sendMessage("quote_add_symbols", [qsl] + self.symbols)
        #print(f" Subscribed to symbols: {self.symbols}")

        await self.sendMessage("quote_fast_symbols", [qs] + self.symbols)
        #print(f" Fast subscription done.")

        #print(f"Subscribed to symbols: {self.symbols}")

    # Start connection
    async def connect(self):
        print("Attempting WebSocket connection...")
        try:
            async with websockets.connect("wss://prodata.tradingview.com/socket.io/websocket", origin="https://www.tradingview.com") as websocket:
                self.connection = websocket
                print("Connected to WebSocket")
                self.connected = True
                await self.waitForMessages()
        except Exception as e:
            print(f"Websocket connection failed: {e}")
            await asyncio.sleep(30)
            await self.connect()

    # Loop waiting for messages
    async def waitForMessages(self):
        await self.authenticate()
        if self.save and not self.connected:
            await self.connectToDatabase()
        #print(" WebSocket connection established, waiting for messages...")

        while self.run:
            messages = await self.readMessage(await self.connection.recv())
            #print(f" Received raw message: {message}")
            for message in messages:
                self.parseMessage(message)

    # Parse incoming messages
    def parseMessage(self, message):

        #print(f"Received message: {message}")
        try:
            message['m']
        except KeyError:
            return

        if message['m'] == "qsd":
            self.forTicker(message)

    # Parse ticker data
    def forTicker(self, receivedData):
        

        symbol = receivedData['p'][1]['n']
        data = receivedData['p'][1]['v']
        #print(f"Received ticker data: {data}")

        items = {
            "volume": "volume",
            "price": "lp",
            "changePercentage": "chp",
            "change": "ch",
            "time": "lp_time"
        }

        for key, data_key in items.items():
            value = data.get(data_key)
            if value is not None:
                self.states[symbol][key] = value

        if self.verbose:
            self.saves += 1

# Send status updates every 5 seconds
    async def giveAnUpdate(self):
        while self.run:  # Run only while active
            await asyncio.sleep(5)
            print(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}: Watching {len(self.symbols)} tickers → received {self.saves} updates")
            self.saves = 0
        print(" Stopping status updates")  # Debug


    def start(self):
        self.loop = asyncio.new_event_loop()

        def _start(loop):
            asyncio.set_event_loop(loop)
            self.run = True

            #print(" Event loop started")  # Debug

            # Create and run the main WebSocket connection
            self.task = loop.create_task(self.connect())
            #print(" WebSocket connection task created")  # Debug

            # Run the update function if verbose mode is enabled
            if self.verbose:
                    self.updateTask = loop.create_task(self.giveAnUpdate())
                    #print(" Status update task created")  # Debug

            try:
                loop.run_forever()
            except Exception as e:
                print(f" Event loop error: {e}")

        # Start in a separate thread
        t = threading.Thread(target=_start, args=(self.loop,))
        t.start()
        self.thread = t

        #print(" Background thread started")  # Debug

        # Register signal handlers for clean exit
        signal.signal(signal.SIGINT, self.cleanup_on_exit)
        signal.signal(signal.SIGTERM, self.cleanup_on_exit)


    # Stop ticker
    def stop(self):
        self.run = False
        self.task.cancel()
        if self.verbose:
            self.updateTask.cancel()
        self.loop.stop()
        self.thread.join()

    def cleanup_on_exit(self, sig, frame):
        print(f"Received signal {sig}. Cleaning up before exit...")

        # Gracefully stop any async tasks
        loop = asyncio.get_event_loop()
        
        if loop.is_running():
            tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
            
            for task in tasks:
                task.cancel()
            
            print(f"Waiting for {len(tasks)} tasks to finish...")
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))

        # Call self.stop() to clean up resources
        self.stop()

        # Properly exit
        print("Cleanup complete. Exiting now.")
        sys.exit(0)
    



# class TradingViewSession:
#     """TradingView WebSocket Session. Handles connection, ticker processing, and optional data storage."""

#     def __init__(self, symbols, should_save=False, db_name="database.db", use_split_symbols=False, enable_verbose=False):
#         self.symbols = symbols if isinstance(symbols, list) else [symbols]
#         self.connection = None
#         self.session_id = f"cs_{generate_random_token()}"
#         self.quote_session = f"qs_{generate_random_token()}"
#         self.subscribers = {symbol: [] for symbol in self.symbols}
#         self.verified = False
#         self.should_save = should_save
#         self.db_name = db_name
#         self.use_split_symbols = use_split_symbols
#         self.enable_verbose = enable_verbose
#         self.states = {symbol: self._initialize_symbol_state() for symbol in self.symbols}
#         self.db_connection = None
#         self.last_message_time = 0
#         self.event_listeners = []
#         self.history = {symbol: deque(maxlen=100) for symbol in self.symbols}  # Stores the last 100 price updates
#         self.reconnect_attempts = 0
#         self.max_reconnect_attempts = 5

#     def _initialize_symbol_state(self):
#         """Initializes the ticker state."""
#         return {"volume": 0, "price": 0, "change": 0, "changePercentage": 0, "time": 0}

#     def connect_to_database(self):
#         """Connects to SQLite and creates tables if needed."""
#         if self.should_save:
#             self.db_connection = sqlite3.connect(self.db_name)
#             self._create_database_tables()

#     def _create_database_tables(self):
#         """Creates database tables."""
#         if self.use_split_symbols:
#             for symbol in self.symbols:
#                 self.db_connection.execute(f"""CREATE TABLE IF NOT EXISTS '{symbol}' (
#                     volume REAL NOT NULL,
#                     price REAL NOT NULL,
#                     timestamp INTEGER NOT NULL
#                 )""")
#         else:
#             self.db_connection.execute("""CREATE TABLE IF NOT EXISTS ticker_data (
#                 volume REAL NOT NULL,
#                 price REAL NOT NULL,
#                 ticker TEXT NOT NULL,
#                 timestamp INTEGER NOT NULL
#             )""")

#     def insert_ticker_data(self, volume, price, ticker, timestamp=None):
#         """Inserts ticker data into the database."""
#         if not self.db_connection:
#             print("Database connection is not initialized.")
#             return

#         timestamp = timestamp or current_epoch_time()

#         if self.enable_verbose:
#             print(f"Inserting data: {ticker} | Volume: {volume} | Price: {price}")

#         self.db_connection.execute("INSERT INTO ticker_data VALUES (?, ?, ?, ?)", (volume, price, ticker, timestamp))
#         self.db_connection.commit()

#     def subscribe(self, symbol, callback):
#         """Subscribes a callback function to a symbol."""
#         if symbol not in self.subscribers:
#             self.subscribers[symbol] = []
#         self.subscribers[symbol].append(callback)

#     def unsubscribe(self, symbol, callback):
#         """Unsubscribes a callback function from a symbol."""
#         if symbol in self.subscribers and callback in self.subscribers[symbol]:
#             self.subscribers[symbol].remove(callback)

#     async def _connect(self):
#         """Establishes a WebSocket connection with TradingView."""
#         if self.connection:
#             await self.connection.close()
#             print("Previous WebSocket connection closed. Reconnecting...")

#         try:
#             self.connection = await websockets.connect(
#                 "wss://data.tradingview.com/socket.io/websocket",
#                 origin="https://www.tradingview.com"
#             )
#             print("Connected to TradingView WebSocket.")
#             self.reconnect_attempts = 0  # Reset reconnect attempts
#             await self._authenticate()
#             await self._listen()
#         except Exception as e:
#             self.reconnect_attempts += 1
#             if self.reconnect_attempts >= self.max_reconnect_attempts:
#                 print("Max reconnect attempts reached. Exiting.")
#                 return
#             print(f"Connection error: {e}. Retrying in {self.reconnect_attempts * 5} seconds...")
#             await asyncio.sleep(self.reconnect_attempts * 5)
#             await self._connect()

#     async def _authenticate(self):
#         """Authenticates with TradingView's WebSocket."""
#         await self._send_message("set_auth_token", ["unauthorized_user_token"])
#         await asyncio.sleep(2)

#         await self._send_message("chart_create_session", [self.session_id, ""])
#         await asyncio.sleep(2)

#         await self._send_message("quote_create_session", [self.quote_session])
#         await asyncio.sleep(2)

#         await self._send_message("quote_set_fields", [self.quote_session, "lp", "ch", "chp", "volume"])
#         await asyncio.sleep(2)

#         await self._send_message("quote_add_symbols", [self.quote_session] + self.symbols)
#         print("Successfully authenticated and subscribed to symbols.")

#     async def _listen(self):
#         """Listens for incoming WebSocket messages and maintains a heartbeat."""
#         while True:
#             try:
#                 message = await self.connection.recv()
#                 message = re.sub(r"~m~\d+~m~", "", message)
#                 self._parse_message(message)

#                 # Send ping every 30 seconds
#                 await asyncio.sleep(30)
#                 await self._send_message("ping", [])
#             except websockets.ConnectionClosed:
#                 print("WebSocket closed. Reconnecting...")
#                 await self._connect()
#             except Exception as e:
#                 print(f"Error in WebSocket: {e}")
#                 await self._connect()

#     def _parse_message(self, message):
#         """Parses WebSocket messages and updates subscribers."""
#         try:
#             if len(message) > 20:
#                 data = json.loads(message)
#                 if data.get('m') == 'qsd' and isinstance(data.get('p'), list):
#                     payload = data['p']
#                     if len(payload) > 1 and isinstance(payload[1], dict):
#                         symbol = payload[1].get('n')
#                         ticker_data = payload[1].get('v', {})

#                         # Store history
#                         self.history[symbol].append(ticker_data.get("lp", 0))

#                         # Notify event listeners
#                         for callback in self.subscribers.get(symbol, []):
#                             callback(symbol, ticker_data)

#                         # Save to database if enabled
#                         if self.should_save:
#                             self.insert_ticker_data(ticker_data.get("volume", 0), ticker_data.get("lp", 0), symbol)
#         except json.JSONDecodeError:
#             pass


# class ZerodhaSession(Session):
#     pass

# if __name__ == '__main__':
#     samco_settings = get_samco_settings()
#     samco_body = dict(userId = samco_settings.SAMCO_USER_ID, 
#                       password = samco_settings.SAMCO_PASSWORD,
#                       yob = samco_settings.SAMCO_YOB)
#     samco = SamcoSession(samco_body)
#     print(samco.is_authenticated())
    
import pandas as pd
import schedule
import time
import asyncio
import aiohttp
from datetime import datetime as dt
from interface import Strategy
from sessions import tradingview_session
from tradeAppLogin import TradingViewSession
from tradeAppData import TradingViewDataExtraction
from utils import send_telegram_message




def get_tv_data(symbol):
    trading_session = TradingViewSession(symbol)  #  Create TradingViewSession
    tv_data = TradingViewDataExtraction(symbol, trading_session)  #  Pass session to tv_data
    return trading_session, tv_data

class MACDStrategy():
    def __init__(self, symbol, trading_session, tv_data, alpha: float = 0.002):
        self.symbol = symbol
        self.trading_session = trading_session
        self.tv_data = tv_data
        self.aplha = alpha # Factor to determine the target price and stop loss. Default is 0.002 (0.2 % change)
        self.entry_price = 0.00
        self.Target_price = 0.00
        self.Stop_loss = 0.00
        self.prev_price = self.tv_data.extract_ltp()
        self.pos_status = None
        self.trade_pos = None
        self.trade_count = 0
        self.Net_result = 0.00
        self.prev_dir = None
        self.mtm = 0.00
        self.trading_session.start()

        # Scheduling tasks
        schedule.every(10).minutes.do(self.trade_mis)
        for minute in range(0, 60, 1):  # Runs every 5 minutes
            schedule.every().hour.at(f"{minute:02d}:00").do(self.get_entry_prices)

    def trade_mis(self):
        msg = f"|| Total Trades so far: {self.trade_count} || Total profit/Loss(-): {self.Net_result} ||"
        print("----------------------------------------------------------------------")
        print(f"\n| Total Trades so far: {self.Net_result} |")
        print("----------------------------------------------------------------------")
        send_telegram_message(msg)

    def get_entry_prices(self):
        a, b, c = self.tv_data.calculate_entry_prices()
        print("----------------------------------------------------------------------")
        print(f"|| Entry price: {a} | Direction: {b} | Time: {c} ||")
        print("----------------------------------------------------------------------")

    def print_msg(self, msg):
        print("=========================================================================")
        print(f"|| {msg} ||")
        print("=========================================================================")
    
    def cross_above(self, prev, ltp, trigger):
        return (trigger > prev) and (trigger < ltp)

    def cross_below(self, prev, ltp, trigger):
        return (trigger > prev) and (trigger < ltp)
    
    def calc_target_stoploss(self, price: float, direction: str):
        '''
           Calculates the target price and stop loss based on price and direction.
        
           Args: 
                price (float): The current market price.
                Direction (str): 'Buy' for a buy position
                                 'Sell' for a sell position

            Returns: 
                    tuple: (Target_price, Stop_loss)
        
        '''
        try:    
            if direction == 'Buy':
                self.Target_price = round(price * (1 + self.alpha), 2)
                self.Stop_loss = round(price * (1 - self.alpha), 2)

            elif direction == 'Sell':
                self.Target_price = round(price * (1 - self.alpha), 2)
                self.Stop_loss = round(price * (1 + self.alpha), 2)
        except Exception as e:
            print(f"Error in calc_target_stoploss: {e}")
                

    def run_strategy(self):
        while True:
            temp = self.trading_session.states
            price = temp[self.symbol]['price']
            
            if price != self.prev_price:
                print(f"LTP: {price} | Prev_Price: {self.prev_price} | Trigger_price: {self.tv_data.ep} | "
                      f"Direction: {self.tv_data.dir} | Target price: {self.Target_price} | "
                      f"Entry price: {self.entry_price} | Stop loss: {self.Stop_loss} | Pos status: {self.pos_status}")

                if self.pos_status is None:
                    if self.tv_data.dir == "Buy" and self.cross_above(self.prev_price, price, self.tv_data.ep):
                        self.pos_status = "Open"
                        self.entry_price = price
                        self.calc_target_stoploss(price, self.tv_data.dir)
                        self.trade_pos = "Buy"
                        msg = f"Position of Buy Taken at {price}, Target: {self.Target_price}, Stop Loss: {self.Stop_loss}"
                        send_telegram_message(msg)
                        self.trade_count += 1
                        self.print_msg(msg)

                    if self.tv_data.dir == "Sell" and self.cross_below(self.prev_price, price, self.tv_data.ep):
                        self.pos_status = "Open"
                        self.entry_price = price
                        self.calc_target_stoploss(price, self.tv_data.dir)
                        self.trade_pos = "Sell"
                        msg = f"Position of Sell Taken at {price}, Target: {self.Target_price}, Stop Loss: {self.Stop_loss}"
                        send_telegram_message(msg)
                        self.trade_count += 1
                        self.print_msg(msg)
                else:
                    self.mtm = price - self.entry_price if self.trade_pos == "Buy" else self.entry_price - price
                    print(f"MTM: {self.mtm}")

                    if self.prev_dir != self.tv_data.dir:
                        msg = f"Trend Changed: {self.trade_pos} Position at {self.entry_price}, with Profit/Loss(-) {self.mtm} is closed"
                        send_telegram_message(msg)
                        self.Net_result += price - self.entry_price
                        self.entry_price = self.Target_price = self.Stop_loss = self.mtm = 0.00
                        self.pos_status = self.trade_pos = None
                        self.print_msg(msg)
                    else:
                        if self.trade_pos == "Buy" and self.cross_above(self.prev_price, price, self.Target_price):
                            msg = f"Buy Position at {self.entry_price}, with Profit: {price - self.entry_price} is closed"
                            send_telegram_message(msg)
                            self.Net_result += price - self.entry_price
                            self.entry_price = self.Target_price = self.Stop_loss = 0.00
                            self.pos_status = self.trade_pos = None
                            self.print_msg(msg)

                        elif self.trade_pos == "Buy" and self.cross_below(self.prev_price, price, self.Stop_loss):
                            msg = f"Buy Position at {self.entry_price}, closed with Loss of: {price - self.entry_price}"
                            send_telegram_message(msg)
                            self.Net_result += price - self.entry_price
                            self.entry_price = self.Target_price = self.Stop_loss = 0.00
                            self.pos_status = self.trade_pos = None
                            self.print_msg(msg)

                        elif self.trade_pos == "Sell" and self.cross_below(self.prev_price, price, self.Target_price):
                            msg = f"Sell Position at {self.entry_price}, Profit: {self.entry_price - price}"
                            send_telegram_message(msg)
                            self.entry_price = self.Target_price = self.Stop_loss = 0.00
                            self.pos_status = self.trade_pos = None
                            self.print_msg(msg)

                        elif self.trade_pos == "Sell" and self.cross_above(self.prev_price, price, self.Stop_loss):
                            msg = f"Sell Position at {self.entry_price}, Loss: {self.entry_price - price}"
                            send_telegram_message(msg)
                            self.Net_result += price - self.entry_price
                            self.entry_price = self.Target_price = self.Stop_loss = 0.00
                            self.pos_status = self.trade_pos = None
                            self.print_msg(msg)

                self.prev_price = price
                self.prev_dir = self.tv_data.dir
                schedule.run_pending()

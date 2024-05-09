import datetime,requests,zipfile,os,json,random,multiprocessing,re,string
import nsepython as n1 
from tvDatafeed import TvDatafeed, Interval 
import pandas as pd
from ta.volatility import BollingerBands as bb 
from io import BytesIO,StringIO
from zipfile import ZipFile
from tabulate import tabulate
from telegram import Bot
from datetime import datetime, timedelta
from websocket import create_connection

import websocket
import threading


global user,pwd,factor,api,tkn, s_token
temp = "working"
s_token = None

def TV_login():
    user = "Recklessgod108"
    pwd = "Fin@9845128002"
    tv = TvDatafeed(user,pwd)
    return(tv)

def tv_quote(sym,tv):
    temp = tv.get_hist(sym,exchange="NSE",interval=Interval.in_1_minute,n_bars=1)
    ltp = temp['close'][-1]
    return(ltp)

def tv_open_price(sym,tv):
    temp = tv.get_hist(sym,exchange="NSE",interval=Interval.in_daily,n_bars=1)
    o = temp['open'][-1]
    return(o)

    


class trade:
    def __init__(self,sym,trend):
        self.sym= sym
        self.sym_fut = None
        self.sym_otp = None
        self.target =None
        self.stop_loss = None
        self.trade_status = None
        self.entry_fut = None
        self.entry_prine = None
        self.ltp = None
        self.previous_ltp = None
        self.exh = None
        self.data_interval = None
        self.sym_type = None
        self.strike_price = None
        self.open_price = None
        self.trade_side = None
        self.trend = trend
        self.TVuser = None
        self.TVpwd = None
        self.TVsym = None
        self.opt_ltp = None
        self.TV_ltp =None
        self.TVmarket = None
        
        
    def script_name(self):
        print(self.sym)
        return(self.sym)
    
    def update_ltp(self, tvs_instance):
        # Update ltp with the latest price from TVS instance
        self.ltp = tvs_instance.ltp
        
    
    def cross_above(self):
        if self.trend == "CE" :
            if self.ltp>self.entry_prine:
                if self.previous_ltp<self.entry_prine:
                    temp = s_quote(self.sym_otp,s_Token,"NFO")
                    self.opt_ltp = temp['lastTradedPrice']
                    channel_msg("Trigger crossed. Position taken:",self.sym_otp," at ",self.opt_ltp)
                    print("crossed above")
                    self.trade_status = "Open"                                       
        pass
    
    def cross_below(self):
        print("crossed below")
        pass
    
    def select_option(self,df):
        temp = df[(df['name']==sym.upper())]
        
        
        
    def calculate_entry_price(self,token,short_window=12, long_window=26, signal_window=9):
        data = s_ohlc(self.sym,token,self.exh,'15')
        data_list =data['close'].tolist()
        data_list = pd.DataFrame(data_list, columns=['close'])
        short_ema = data_list.ewm(span=short_window, min_periods=1, adjust=False).mean()
        long_ema = data_list.ewm(span=long_window, min_periods=1, adjust=False).mean()
        macd_line = short_ema - long_ema
        signal_line = macd_line.ewm(span=signal_window, min_periods=1, adjust=False).mean()
        macd_histogram = macd_line - signal_line
    
        m = macd_histogram.tail(3)
        a,b,c = m.values
        a= float(a)
        b = float(b)
        c = float(c)
        h = data['high'].tail(1)
        l = data['low'].tail(1)
        global entry_price,target_price, exit_price
        
    
        
        print(self.sym,a,b,c)
        if a>b<c:
            self.entry_price = round_to_nearest_0_05(float(h.values))
            #self.target = round_to_nearest_0_05(float(h.values)+20)
            #self.exit_price = round_to_nearest_0_05(float(h.values)-20)
            self.sym_type ="CE"
            print(self.sym, ": Upside trend, Entry price :",float(h.values)," Exit Price : ",float(l.values))
            
        if a<b>c:
            entry_price = round_to_nearest_0_05(float(l.values))
            #target_price = round_to_nearest_0_05(float(l.values)-20)
            #exit_price = round_to_nearest_0_05(float(l.values)+20)
            self.sym_type = "PE"
            print(self.sym, ": Down trend, Entry price :",float(l.values)," Exit Price : ",float(h.values))
        
           
        
def round_to_nearest_0_05(number):
    rounded_number = round(number, 2)  # Round to 2 decimals
    adjusted_number = round(rounded_number / 0.05) * 0.05  # Round to the nearest 0.05
    return adjusted_number

def df_download():
    url = "https://developers.stocknote.com/doc/ScripMaster.csv"
    response = requests.get(url)
    if response.status_code == 200:
        # Read the content of the response as a string
        csv_data = response.text
        
        # Load the string data into a Pandas DataFrame
        df = pd.read_csv(StringIO(csv_data))
        
        # Now you can work with the DataFrame 'df'
        #print(df)  # Display the first few rows of the DataFrame
        return(df)
    else:
        print("Failed to fetch data from the URL:", response.status_code)



async def send_table_to_telegram(bot, table):
    TELEGRAM_BOT_TOKEN = '6826962569:AAEVHzPQnNXNuBB0mGcCiaDzLMARvk79Cpc'
    
    TELEGRAM_CHAT_ID = '-1002138820012'    
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f'<pre>{table}</pre>', parse_mode='HTML')


def expiry_date():
    temp = n1.expiry_list("INFY")[0]
    temp = datetime.strptime(temp, '%d-%b-%Y').strftime('%Y-%m-%d')
    return temp

def channel_msg(t):
    url = "https://api.telegram.org/bot6826962569:AAEVHzPQnNXNuBB0mGcCiaDzLMARvk79Cpc/"
    sm_url = "https://api.telegram.org/bot6826962569:AAEVHzPQnNXNuBB0mGcCiaDzLMARvk79Cpc/sendMessage?chat_id=-1002138820012&text="
    i_url = "https://ibb.co/Ph6Jct8"
    x = requests.post(sm_url+t)
    TELEGRAM_BOT_TOKEN = '6826962569:AAEVHzPQnNXNuBB0mGcCiaDzLMARvk79Cpc'
    
    # Replace with your Telegram chat ID
    TELEGRAM_CHAT_ID = '-1002138820012'
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=t, parse_mode='HTML')


    
    
def channel_img(img):
    url = "https://api.telegram.org/bot6826962569:AAEVHzPQnNXNuBB0mGcCiaDzLMARvk79Cpc/"
    is_url = "https://api.telegram.org/bot6826962569:AAEVHzPQnNXNuBB0mGcCiaDzLMARvk79Cpc/sendPhoto?chat_id=-1002138820012&text="
    i_url = img
    x = requests.post(is_url+i_url)


def login_samco():
    global s_token
    s_token =""
    headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
    
    requestBody={
      "userId": "DA39226",
      "password": "Fin@128002",
      "yob": "1980"
    }
    
    r = requests.post('https://api.stocknote.com/login'
    , data=json.dumps(requestBody)
    , headers = headers)
    print(r.json())
    
    s = r.json()['sessionToken']
    temp = r.json()['statusMessage']
    print(s)
    if temp == 'Session Expired. Please login again.':
        logout(s)
        r = requests.post('https://api.stocknote.com/login'
        , data=json.dumps(requestBody)
        , headers = headers)
        print(r.json())
        
        s_token = r.json()['sessionToken']
        temp = r.json()['statusMessage']
        print('session : ',s_token)
        token = s_token
    return s

def s_get_hist(sym,token,exh,days):
    days = 4
    today = datetime.today()
    From_date = today - timedelta(days)
    From_date = From_date.strftime('%Y-%m-%d')
    
    print("From Date : ",From_date)
    
    headers = {
      'Accept': 'application/json',
      'x-session-token': token
    }
    
    r = requests.get('https://api.stocknote.com/history/candleData', params={
      'symbolName': sym, 'exchange': exh, 'fromDate': From_date
    }, headers = headers)
    print(r.json())
    temp = pd.DataFrame(r.json()['historicalCandleData'])
    #print(temp)
    return(temp)


def s_fetch_data(sym, token,trend):
    sym_fut = sym + "24APRFUT"
    s1 = s_get_hist(sym,token,'NSE',30) # 30 days 
    s2 = s_ohlc(sym_fut,token,'NFO','15') # 15 mins candle data
    s1.to_csv(str(sym)+".csv")
    s2.to_csv(str(sym)+".csv")
    print(s1)
    print(s2)

    t_temp = bb(s1['close'], 20, 2)
    #temp = t_temp.bollinger_hband()
    t_s1_bbtop = t_temp.bollinger_hband().iloc[-1]
    t_s1_bbbot = t_temp.bollinger_lband().iloc[-1]
    t_temp = bb(s1['close'], 20, 0.7)
    t_s2_bbtop = t_temp.bollinger_hband().iloc[-1]
    t_s2_bbbot = t_temp.bollinger_lband().iloc[-1]
    target_time = pd.to_datetime("09:15:00").time()
    #temp_a = 
    #print("a : ",float(s1.iloc[-1]["open"]))
    #print("b : ",float(s1.iloc[-2]["close"]))
    #print("c : ",float(s1.iloc[-2]["close"] * 100))
    a_temp = float((s1.iloc[-1]["open"]) - float(s1.iloc[-2]["close"]))
    b_temp = float(s1.iloc[-2]["close"])
    temp = (a_temp/b_temp)*100
    #temp = [float((s1.iloc[-1]["open"]) - float(s1.iloc[-2]["close"])) / float(s1.iloc[-2]["close"])] * 100
    
    target_row = s2[s2.index.time == target_time]     
    op_price = target_row.iloc[-1]['open']
    high = target_row.iloc[-1]['high']
    low = target_row.iloc[-1]['low']
    close = target_row.iloc[-1]['close']
    selected = False
    if (trend == 1) and (t_s2_bbtop < op_price ) and (close>op_price) :
        selected = True
    
    if (trend == 2) and (op_price < t_s2_bbbot) and (close<op_price) :
        selected = True
                
        
        
    return {
        "sym": sym,
        "open": op_price, #s1.iloc[-1]["open"],
        "High": high,
        "Low" : low,
        "15-Min Close" : close,
        "prev_close": s1.iloc[-2]["close"],
        "bbtop1": t_s1_bbtop,
        "bbtop2": t_s2_bbtop,
        "bbbottom1": t_s1_bbbot,
        "bbbottom2": t_s2_bbbot,
        "op_pc_perc": temp,
        "Selected" : selected,
        "trend_direction": "Upside" if trend == 1 else "Downside"
    }


def s_quote(sym,token, exh):
    headers = {
      'Accept': 'application/json',
      'x-session-token': token
    }
    params={'exchange' :exh,'symbolName': sym }
    
    r = requests.get('https://api.stocknote.com/quote/getQuote', params=params, headers = headers)
    temp = r.json()
    if temp['status']=='Success':
        ltp = float(r.json()['lastTradedPrice'])
    else:
        print(sym ," Error : ", r.json()['statusMessage'])
        ltp = 0
    #print("sym : ",sym,"LTP : ",temp)
    return (temp,ltp)


def mcx_quote(sym,token):
    headers = {
      'Accept': 'application/json',
      'x-session-token': token
    }
    params={'exchange' :'MFO','symbolName': sym }
    
    r = requests.get('https://api.stocknote.com/quote/getQuote', params=params, headers = headers)
    
    return (r.json())


def scan1(token):
    temp = n1.fnolist()
    print("1 :",temp)
    r_list = ['NIFTY', 'NIFTYIT', 'BANKNIFTY']
    sym_list = [item for item in temp if item not in r_list]
    count = 0
    data = []
    #temp = n1.expiry_list('INFY')[0]
    #temp = temp[3:-5].upper()
    #print(temp)
   
    for item in sym_list:
        count += 1
        print("Data of ",item," ",count," of ",len(sym_list))
        sym = str(item)  +"24MAYFUT"
        sym1=sym.upper()
        sym = item.replace("&","_").replace("-","_")
        temp,ltp = s_quote(sym1,token,exh="NFO")
        if temp['status']=='Success':
            op = float(temp['openValue'])
            pc = float(temp['previousClose'])
            print("OP :",op,"PC: ",pc)
            diff = (pc - op) / pc
            #print(sym,op,pc,diff)
            temp = (sym,op,pc,diff)
            data.append(temp)
        else:
            print(sym1," gave an Error : ",temp['statusMessage'])
        
    temp_data = pd.DataFrame(data, columns=['Script', 'Open', 'Prevclose', 'diff'])
    temp_data['Rank'] = temp_data['diff'].rank()
    temp_data_sorted = temp_data.sort_values(by='Rank', ascending=True)
    top_upside = temp_data_sorted.head(6)
    top_downside = temp_data_sorted.tail(6)

    print(top_upside)
    print()
    print(top_downside)
    temp_data_sorted.to_csv("result.csv")
    top_upside.to_csv("top_upside.csv")
    top_downside.to_csv("top_downside.csv")
    return top_upside, top_downside

def fetch_data(tv, sym, trend):
    try:
        s1 = tv.get_hist(sym, "NSE", Interval.in_daily, n_bars=100, fut_contract=1)
        s2 = tv.get_hist(sym, "NSE", Interval.in_15_minute, n_bars=100, fut_contract=1)
    except Exception as e:
        print("An error occurred:", str(e))
        return None
    print(s1,s2)
    t_temp = bb(s1['close'], 20, 2)
    t_s1_bbtop = t_temp.bollinger_hband()[-1]
    t_s1_bbbot = t_temp.bollinger_lband()[-1]
    t_temp = bb(s1['close'], 20, 0.7)
    t_s2_bbtop = t_temp.bollinger_hband()[-1]
    t_s2_bbbot = t_temp.bollinger_lband()[-1]
    target_time = pd.to_datetime("09:15:00").time()
    temp = ((s1.iloc[-1]["open"] - s1.iloc[-2]["close"]) / s1.iloc[-2]["close"]) * 100
    target_row = s2[s2.index.time == target_time]     
    op_price = target_row.iloc[-1]['open']
    high = target_row.iloc[-1]['high']
    low = target_row.iloc[-1]['low']
    close = target_row.iloc[-1]['close']
    selected = False
    if (trend == 1) and (t_s2_bbtop < op_price ) and (close>op_price) :
        selected = True
    
    if (trend == 2) and (op_price < t_s2_bbbot) and (close<op_price) :
            selected = True
                
        
        
    return {
        "sym": sym,
        "open": op_price, #s1.iloc[-1]["open"],
        "High": high,
        "Low" : low,
        "15-Min Close" : close,
        "prev_close": s1.iloc[-2]["close"],
        "bbtop1": t_s1_bbtop,
        "bbtop2": t_s2_bbtop,
        "bbbottom1": t_s1_bbbot,
        "bbbottom2": t_s2_bbbot,
        "op_pc_perc": temp,
        "Selected" : selected,
        "trend_direction": "Upside" if trend == 1 else "Downside"
    }


    
def filter1(l1,l2,token):
    df_up=[]
    df_dn = []
    user = 'Recklessgod108'
    pwd = "Fin@9845128002"
    tv = TvDatafeed(user,pwd)
    
    print(l1)
    print(l2)
    for item in l1['Script']:
        #sym = item[1]
        results_df_up = fetch_data(tv,item,1)
        df_up.append(results_df_up)
    
    for item in l2['Script']:
        results_df_dn = fetch_data(tv,item,2)
        df_dn.append(results_df_dn)
    
    df_up = pd.DataFrame(df_up)
    df_up.to_csv("top_upside.csv")
    print(df_up)
    
    df_dn = pd.DataFrame(df_dn)
    df_dn.to_csv("top_downside.csv")
    print(df_dn)
    #selected_df_up = df_up[df_up['Selected']]
    ##print(selected_df_up)
    result_df_up = df_up.loc[df_up['Selected'] == True, ['sym', 'High']]
    table = result_df_up.to_markdown(index=False)
    
    
    TELEGRAM_BOT_TOKEN = '6826962569:AAEVHzPQnNXNuBB0mGcCiaDzLMARvk79Cpc'
    
    # Replace with your Telegram chat ID
    TELEGRAM_CHAT_ID = '-1002138820012'
    
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f'<pre>{table}</pre>', parse_mode='HTML')
    
    print("result up:",result_df_up)
    
    #selected_df_dn = df_dn[df_dn['Selected']]
    result_df_dn = df_dn.loc[df_dn['Selected'] == True, ['sym', 'Low']]
    table = result_df_dn.to_markdown(index=False)
    
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f'<pre>{table}</pre>', parse_mode='HTML')
        
    
    
    print("result dn: ",result_df_dn)
    #channel_msg("Upside:"+str(result_df_up))
    #channel_msg("Downside:"+str(result_df_dn))
        
        
    return result_df_up,result_df_dn



def s_ohlc(sym,token,exh,i):

    if exh == "NFO":
        temp = n1.expiry_list(sym)[0]
        temp = temp[3:-5].upper()
        sym = sym+"24MAYFUT"
        
    elif exh == "MFO":
        sym = sym+"24MAYFUT"
        
    headers = {
      'Accept': 'application/json',
      'x-session-token': token
    }
    # Get the current date and time
    current_datetime = datetime.now()
    
    # Calculate the date and time 5 days ago
    five_days_ago = current_datetime - timedelta(days=3)
    
    # Format the date and time as required
    formatted_date = five_days_ago.strftimex
    
    
    params={'exchange' : exh,'symbolName': sym, 'fromDate': formatted_date , 'interval':i}
    r = requests.get('https://api.stocknote.com/intraday/candleData', params=params, headers = headers)
    temp = r.json()
    if temp['status']=='Success':
        temp = temp['intradayCandleData']
        temp = pd.DataFrame(temp)
        temp_dt = temp.iloc[-1].dateTime
        date_format = '%Y-%m-%d %H:%M:%S'
        temp_m = datetime.strptime(temp_dt, date_format)
        return(temp)    
    else:
        print("Error : ",  temp['statusMessage'])

class TVS:
    def __init__(self):
        self.ltp = None
        self.ws = None

    def search(self, query, type):
        # type = 'stock' | 'futures' | 'forex' | 'cfd' | 'crypto' | 'index' | 'economic'
        # query = what you want to search!
        # it returns first matching item
        res = requests.get(
            f"https://symbol-search.tradingview.com/symbol_search/?text={query}&type={type}"
        )
        if res.status_code == 200:
            res = res.json()
            print(res[0])
            assert len(res) != 0, "Nothing Found."
            return res[0]
        else:
            print("Network Error!")
            exit(1)

    def generateSession(self):
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters) for i in range(stringLength))
        return "qs_" + random_string

    def prependHeader(self, st):
        return "~m~" + str(len(st)) + "~m~" + st

    def constructMessage(self, func, paramList):
        return json.dumps({"m": func, "p": paramList}, separators=(",", ":"))

    def createMessage(self, func, paramList):
        return self.prependHeader(self.constructMessage(func, paramList))

    def sendMessage(self, ws, func, args):
        ws.send(self.createMessage(func, args))

    def sendPingPacket(self, ws, result):
        pingStr = re.findall(".......(.*)", result)
        if len(pingStr) != 0:
            pingStr = pingStr[0]
            ws.send("~m~" + str(len(pingStr)) + "~m~" + pingStr)

    def socketJob(self):
        while True:
            try:
                result = self.ws.recv()
                if "quote_completed" in result or "session_id" in result:
                    continue
                Res = re.findall("^.*?({.*)$", result)
                if len(Res) != 0:
                    jsonRes = json.loads(Res[0])

                    if jsonRes["m"] == "qsd":
                        symbol = jsonRes["p"][1]["n"]
                        price = jsonRes["p"][1]["v"]["lp"]
                        print(f"{symbol} -> {price}")
                        self.ltp = price  # Update the class variable ltp here
                else:
                    # ping packet
                    self.sendPingPacket(self.ws, result)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                exit(0)
            except Exception as e:
                print(f"ERROR: {e}\nTradingView message: {result}")
                continue

    def getSymbolId(self, pair, market):
        data = self.search(pair, market)
        if data['type'] == 'futures':
            symbol_name = data['contracts'][0]['symbol']
        else:
            symbol_name = data["symbol"]

        try:
            broker = data["prefix"]
        except KeyError:
            broker = data["exchange"]
        symbol_id = f"{broker.upper()}:{symbol_name.upper()}"
        print(symbol_id, end="\n\n")
        return symbol_id

    def main(self, pair, market):
        # serach btcusdt from crypto category
        symbol_id = self.getSymbolId(pair, market)

        # create tunnel
        tradingViewSocket = "wss://data.tradingview.com/socket.io/websocket"
        headers = {"Origin": "https://data.tradingview.com"}
        self.ws = websocket.create_connection(tradingViewSocket, header=headers)
        session = self.generateSession()

        # Send messages
        self.sendMessage(self.ws, "quote_create_session", [session])
        self.sendMessage(self.ws, "quote_set_fields", [session, "lp"])
        self.sendMessage(self.ws, "quote_add_symbols", [session, symbol_id])

        # Start job in a new thread
        threading.Thread(target=self.socketJob).start()


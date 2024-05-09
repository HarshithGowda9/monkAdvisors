import sched
import time, asyncio
import base 
import datetime
import requests
from io import StringIO
import pandas as pd


def Strike_price(sym,price):
    price = float(price)
    temp = df[(df['name']==sym.upper())]
    temp = temp[(temp['instrument']=='OPTSTK')]
    temp['strikePrice'] = pd.to_numeric(temp['strikePrice'], errors='coerce')
    temp['diff'] = abs(temp['strikePrice'] - price)
    #print(temp)
    temp = temp.sort_values(by='diff')
    #print(temp)
    
    strike_price = int(temp.iloc[0]['strikePrice'])
    #print(strike_price)
    return(strike_price)

#Initialisation

x = base
token = x.login_samco()
df = x.df_download()
tv = x.TV_login()

#upside scripts
l1 = pd.read_csv("top_downside.csv")
l2 = pd.read_csv("top_upside.csv")

#CE list
up = []
dn = []

temp = l1.loc[l1['Selected']==False,['sym']]
for i in temp.values: up.append(str(i[0]))
temp = l2.loc[l2['Selected']==True,['sym']]
for i in temp.values: up.append(str(i[0]))
print(up)

temp = l1.loc[l1['Selected']==True,['sym']]
for i in temp.values: dn.append(str(i[0]))
temp = l2.loc[l2['Selected']==False,['sym']]
for i in temp.values: dn.append(str(i[0]))
print(dn)
l=[]

for i in up:
    l.append(x.trade(i,"CE"))
for i in dn:
    l.append(x.trade(i,"PE"))
    
print(l)
print(len(l))



for i in range(len(l)):
    l[i].exh = 'NFO'
        
    l[i].sym_fut = l[i].sym+"24MAYFUT"
    l[i].TVsym = l[i].sym+"K2024"
    temp,ltp = x.s_quote(l[i].sym_fut, token, l[i].exh)
    
    if temp['status']== 'Success' :
        print("Sym : ",l[i].sym,"OpenValue : ",temp['openValue'])
        l[i].strike_price = Strike_price(l[i].sym,temp['openValue'])
        print("Option Strike Price : ",l[i].strike_price)
        l[i].sym_opt = l[i].sym+"24MAY"+str(l[i].strike_price)+l[i].trend 
        l[i].calculate_entry_price(token)
        
    else : 
        temp = x.tv_open_price(l[i].TVsym,tv)
        l[i].strike_price = Strike_price(l[i].sym,temp)
        print("Sym : ",l[i].sym,"OpenValue : ",temp['openValue'])
        print("Option Strike Price : ",l[i].strike_price)
        l[i].sym_opt = l[i].sym+"24MAY"+str(l[i].strike_price)+l[i].trend 
        l[i].calculate_entry_price(token)
                

#Step1 repeats every second
def step1():
    for i in range(len(l)):
        if l[i].trade_status==None:
            #if no open trades then check if crossed entry price
            try:
                temp, l[i].ltp = x.s_quote(l[i].sym_fut, token, l[i].exh)
                print("Sym : ",l[i].sym," LTP : ",l[i].ltp)
                            
            except:
                print("Error : ",temp)
                
                temp = x.tv_quote(l[i].TVsym,tv)
                print("Sym : ",l[i].sym," LTP : ",temp)
            
                     
        try :
            temp, ltp = x.s_quote(l[i].sym_opt, token, l[i].exh)
            print("Sym : ",l[i].sym_opt,"Option  LTP : ",temp['lastTradedPrice'])
                                
        except:
            print("Error : ",temp)
                   
            
def step2():
    for item in l:
        item.calculate_entry_price(token)
            



# Initialize the scheduler
scheduler = sched.scheduler(time.time, time.sleep)

def execute_step1():
    step1()
    scheduler.enter(1, 1, execute_step1)  # Schedule the next execution after 1 second

def execute_step2():
    step2()
    now = datetime.datetime.now()
    minutes_to_next_step2 = (15 - (now.minute % 15)) % 15  # Calculate minutes remaining until the next step2
    next_execution_time = now + datetime.timedelta(minutes=minutes_to_next_step2)
    next_execution_time = next_execution_time.replace(second=0, microsecond=0)  # Round down to nearest minute
    delay = (next_execution_time - now).total_seconds()
    scheduler.enter(delay, 1, execute_step2)  # Schedule the next execution at the calculated time

# Schedule the initial executions
scheduler.enter(0, 1, execute_step1)
execute_step2()  # Schedule the first execution of step2

# Start the scheduler
scheduler.run()

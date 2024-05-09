import requests
import json
import schedule
import time
import base  # Import the functions from base.py
import pandas as pd
import asyncio
from tvDatafeed import TvDatafeed, Interval 


#Function to measure execution time
def measure_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time:.2f} seconds")
        return result
    return wrapper

@measure_execution_time
def main():
    up = None
    dn = None

    x = base
    token = x.login_samco()
    print(token)
    print("Task executed at:", time.strftime("%Y-%m-%d %H:%M:%S"))
    up, dn = x.scan1(token) #runs at 9:15
    
    
    
    
    user = 'Recklessgod108'
    pwd = "Fin@9845128002"
    tv = TvDatafeed(user,pwd)
    
    today_dn,today_up=x.filter1(up,dn,token) # run at 9:30
    
    
    
    
if __name__ == "__main__":
    main()

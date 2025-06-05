#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# -*- coding: utf-8 -*-
"""
Created on Fri Aug 18 13:29:49 2023

@author: rajas
"""
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 18 10:13:25 2023

@author: rajas
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 23:12:32 2023

@author: rajas
"""

#!/usr/bin/env python
# coding: utf-8

# In[19]:


import os
from binance.client import Client
import time
import pandas as pd
import requests
from requests.exceptions import ReadTimeout

# Binance API credentials
API_KEY = ''
API_SECRET = ''

# Initialize the Binance client
client = Client(API_KEY, API_SECRET)

# Function to place a order
def place_order(symbol, side,  quantity):
    try:
        exchange_info = client.futures_exchange_info()  # Retrieve information about all trading symbols
        symbol_info = next(s for s in exchange_info['symbols'] if s['symbol'] == symbol)
        lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
        step_size = float(lot_size_filter['stepSize'])
        
        # Round the quantity to the nearest step size
        quantity = round(quantity / step_size) * step_size
        
        #price = round(price, 8)
        quantity=round(quantity, 8)
        order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type=Client.FUTURE_ORDER_TYPE_MARKET,
            #timeInForce=Client.TIME_IN_FORCE_GTC,
            quantity=quantity,
            #price=price
        )
        return order
    except Exception as e:
        print("Error placing order:", e)
        return None

# Function to get the current price of a futures symbol
def get_symbol_price(symbol):
    try:
        ticker = client.futures_ticker(symbol=symbol)
        return float(ticker['lastPrice'])
    except Exception as e:
        print("Error getting symbol price:", e)
        return None

# Function to get the rolling previous day high and low for futures
def get_previous_day_high_low(symbol):
    try:
        klines = client.futures_klines(
            symbol=symbol,
            interval=Client.KLINE_INTERVAL_1MINUTE ,
            limit=1450
            #contractType=contract_type# Fetch 288+1 (including previous day) candles
        )

        df = pd.DataFrame(klines, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        
        df['previous_high'] = df['high'].rolling(window=720, min_periods=1).max().shift(1)
        df['previous_low'] = df['low'].rolling(window=720, min_periods=1).min().shift(1)

        previous_day_high = df.iloc[-1]['previous_high']
        previous_day_low = df.iloc[-1]['previous_low']

        return previous_day_high, previous_day_low
    except Exception as e:
        print("Error getting previous day high and low:", e)
        return None, None
def round_price(price, tick_size):
    return round(price / tick_size) * tick_size
#def check_internet_connection():
    #try:
        #response = requests.get("http://www.google.com", timeout=10)
        #return True
    #except requests.ConnectionError:
        #return False
def check_internet_connection():
    try:
        response = requests.get("http://www.google.com", timeout=5)
        return response.status_code == 200
    except requests.Timeout:
        print("Connection timed out. Retrying...")
        return False
    except requests.RequestException as e:
        print(f"An error occurred: {e}. Retrying...")
        return False

def main():
    symbol = 'BNBUSDT'
    #retries = 3
    #timeout = 10
    open_position = False
    position_side = None
    entry_price = None
    target_price = None
    stop_loss_price = None

    while True:
        
        if check_internet_connection():
            try:
                current_price = get_symbol_price(symbol)
                previous_day_high, previous_day_low = get_previous_day_high_low(symbol)
                print(previous_day_high, previous_day_low)
                print(current_price)
                print(target_price)
                print(stop_loss_price)

                symbol_info = client.get_symbol_info(symbol)
                tick_size = float(symbol_info['filters'][0]['tickSize'])
                
                if current_price is not None and previous_day_high is not None and previous_day_low is not None:
                    if not open_position:
                        if current_price > previous_day_high:
                            print("Price broke previous day high. Placing long order...")
                            quantity = (1/current_price)*201  # Fixed quantity in BTC
                            price = round_price(current_price, tick_size)
                            take_profit = price * 1.008  # 0.8% above entry price
                            stop_loss = price * 0.992   # 0.8% below entry price
                            place_order(symbol, Client.SIDE_BUY, quantity)
                            
                            open_position = True
                            position_side = Client.SIDE_BUY
                            entry_price = price
                            target_price = take_profit
                            stop_loss_price = stop_loss
                        
                        elif current_price < previous_day_low:
                            print("Price broke previous day low. Placing short order...")
                            quantity = (1/current_price)*201  # Fixed quantity in BTC
                            price = round_price(current_price, tick_size)
                            take_profit = price * 0.992  # 0.8% below entry price
                            stop_loss = price * 1.008   # 0.8% above entry price
                            place_order(symbol, Client.SIDE_SELL, quantity)
                            
                            open_position = True
                            position_side = Client.SIDE_SELL
                            entry_price = price
                            target_price = take_profit
                            stop_loss_price = stop_loss
                    else:
                        if (position_side == Client.SIDE_BUY and current_price >= target_price) or (position_side == Client.SIDE_SELL and current_price <= target_price):
                            print("Target price reached. Placing order to close position...")
                            close_quantity = (1/current_price)*201   # Fixed quantity in BTC
                            place_order(symbol, Client.SIDE_SELL if position_side == Client.SIDE_BUY else Client.SIDE_BUY, close_quantity)
                            open_position = False
                            position_side = None
                            entry_price = None
                            target_price = None
                            stop_loss_price = None
                        elif (position_side == Client.SIDE_BUY and current_price <= stop_loss_price) or (position_side == Client.SIDE_SELL and current_price >= stop_loss_price):
                            print("Stop-loss price reached. Placing order to close position...")
                            close_quantity = (1/current_price)*201   # Fixed quantity in BTC
                            place_order(symbol, Client.SIDE_SELL if position_side == Client.SIDE_BUY else Client.SIDE_BUY, close_quantity)
                            open_position = False
                            position_side = None
                            entry_price = None
                            target_price = None
                            stop_loss_price = None
            except Exception as e:
                print("ReadTimeout error. Retrying...",e)
        else:
            print("No internet connection, waiting...")
        
        time.sleep(1)  # Adjust the sleep time as needed

if __name__ == '__main__':
    main()


# In[ ]:





# In[ ]:





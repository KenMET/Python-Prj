#!/bin/python3

# System lib
import os
import sys
import json
import math
import random
import datetime, time
import numpy as np
import pandas as pd
from decimal import Decimal

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../common'%(py_dir))
from config import get_strategy, get_global_config
from database import get_dog_last_price
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log


def get_stategy_handle(target, trade_type):
    strategy_dict = get_strategy(target)
    strategy_type = strategy_dict[trade_type]['class']
    #log.get('backtest').info('get_stategy_handle:%s %s %s'%(target, strategy_type, str(strategy_dict)))
    if strategy_type == 'mean_reversion':
        short = int(strategy_dict[trade_type]['detail']['short_window'])
        long = int(strategy_dict[trade_type]['detail']['long_window'])
        th = float(strategy_dict[trade_type]['detail']['threshold'])
        trade_interval = int(strategy_dict[trade_type]['detail']['cool_down_period'])
        stategy_handle = basic(short, long, th, trade_interval)
    elif strategy_type == 'bollinger':
        window_size = int(strategy_dict[trade_type]['detail']['window_size'])
        k_val = float(strategy_dict[trade_type]['detail']['k_val'])
        probability_limit = float(strategy_dict[trade_type]['detail']['probability_limit'])
        stategy_handle = bollinger(window_size, k_val, probability_limit)
    elif strategy_type == 'xxx':   # to be update
        pass
    return stategy_handle

def generate_basic_strategy_list():
    short_range = range(2, 10+1)
    long_range = range(15, 40+1)
    th_range = range(1, 40+1)  # persentage / 10 (0.1% - 4%)
    interval_range = range(1, 10+1)
    temp_list = []
    for a in th_range:
        for b in long_range:
            for c in short_range:
                for d in interval_range:
                    temp_dict = {
                        'th' : float(a)/10,
                        'short' : int(c),
                        'long' : int(b),
                        'trade_interval' : int(d),
                    }
                    temp_list.append(temp_dict)
    return temp_list

'''
************************************  Rule  ************************************
1. Each strategy class, init to input parameters
    Such as "basic": short, long, th, trade_interval
2. Each strategy calculation factor's I/O data type
    input: DataFrame
    output: DataFrame with Signal column(Buy=1, Sell=-1, Hold=0)
********************************************************************************
'''

class basic:
    def __init__(self, short, long, th, trade_interval):
        self.short = short
        self.long = long
        self.th = th/100
        self.trade_interval = trade_interval
        self.last_signal_day = -trade_interval  # Start from the first day

    def mean_reversion(self, df):
        # Calculate the window average
        df['Short_MA'] = df['Close'].rolling(window=self.short, min_periods=1).mean()
        df['Long_MA'] = df['Close'].rolling(window=self.long, min_periods=1).mean()

        df['Short_MA'] = pd.to_numeric(df['Short_MA'], errors='coerce')
        df['Long_MA'] = pd.to_numeric(df['Long_MA'], errors='coerce')

        # Init Trade signal column
        df['Signal'] = 0

        # Enable thresholds and trade_interval, otherwise it is easy to generate too much transactions
        for i in range(len(df)):
            short_ma = df['Short_MA'].iloc[i]
            long_ma = df['Long_MA'].iloc[i]

            # if trade_interval has expired since the last operation
            if i - self.last_signal_day >= self.trade_interval:
                # If the short window_avg is higher than long window_avg
                # and the gap is greater than the threshold
                # Means that the short increase is large, and consider selling
                if (short_ma - long_ma)/short_ma > self.th:
                    df.loc[i, 'Signal'] = -1
                    self.last_signal_day = i

                # Contrary to above, short window_avg is lower than long window_avg
                elif (long_ma - short_ma)/long_ma > self.th:
                    df.loc[i, 'Signal'] = 1
                    self.last_signal_day = i
            else:
                df.loc[i, 'Signal'] = 0  # No signal is generated during trade_interval

        # Generates an actual buy/sell trading signal, preventing a signal from being repeated over a period of time
        df['Position'] = df['Signal'].diff()

        return df

    
    # Set       threshold = (1 + th)   or   (1 - th)
    # Set       short_df = [219.16 , 219.57]            short_window_size = 3
    # Set       long_df  = [217.8, 219.16 , 219.57]     long_window_size  = 4
    # 满足条件时[x,+∞]会触发sell: (219.16 + 219.57 + x) / 3 = (1 + th) * (217.8 + 219.16 + 219.57 + x) / 4
    # 满足条件时[-∞,x]会触发buy:  (219.16 + 219.57 + x) / 3 = (1 - th) * (217.8 + 219.16 + 219.57 + x) / 4
    # Then [x,+∞] trigger sell:  (sum(short_df) + x) / short_window_size = threshold * (sum(long_df) + x) / long_window_size
    #
    #                 sum(short_df) * long_window_size - threshold * short_window_size * sum(long_df)
    # expect = x = -------------------------------------------------------------------------------------
    #                   threshold * short_window_size - long_window_size
    def probability(self, df, dog_id=None):
        df = self.mean_reversion(df)
        last_index = len(df) - 1
        if last_index - self.last_signal_day < self.trade_interval:
            return 0.1, 0.1  # 仍在冷却期内

        price_column_name = ''
        if 'Price' in df.columns:
            price_column_name = 'Price'
        elif 'Close' in df.columns:
            price_column_name = 'Close'
        else:
            return 0.1, 0.2
        short_df = df[price_column_name].tail(self.short - 1)
        long_df = df[price_column_name].tail(self.long - 1)
        if dog_id == None:
            last = df[price_column_name].tail(1).item()
        else:
            last = get_dog_last_price(dog_id)
        log.get('backtest').info('last:%.2f'%(last))
        #log.get('backtest').info('threshold:%.2f'%(self.th))

        threshold = (1 - self.th)
        expect_buy = sum(short_df) * self.long - threshold * self.short * sum(long_df)
        expect_buy /= threshold * self.short - self.long
        log.get('backtest').info('expect_buy:[0, %.2f]'%(expect_buy))
        
        threshold = (1 + self.th)
        expect_sell = sum(short_df) * self.long - threshold * self.short * sum(long_df)
        expect_sell /= threshold * self.short - self.long
        log.get('backtest').info('expect_sell: [%.2f, +∞]'%(expect_sell))

        steepness = float(get_global_config('price_steepness'))
        trough_probability = 100 * max(0.0, min(1.0, math.exp(-steepness * (last - expect_buy))))
        peak_probability =100 * max(0.0, min(1.0, math.exp(-steepness * (expect_sell - last))))

        return float(trough_probability), float(peak_probability)

class bollinger:
    def __init__(self, window_size, k_val, probability_limit):
        self.window_size = window_size
        self.k_val = k_val
        self.probability_limit = probability_limit
        self.bollinger_list = []

    def probability(self, df, dog_id=None):
        price_column_name = ''
        if 'Price' in df.columns:
            price_column_name = 'Price'
        elif 'Close' in df.columns:
            price_column_name = 'Close'
        else:
            return 0.1, 0.1
        rolling_mean = df[price_column_name].rolling(self.window_size).mean()
        rolling_std = df[price_column_name].rolling(self.window_size).std()
        upper_band = rolling_mean + self.k_val * rolling_std
        lower_band = rolling_mean - self.k_val * rolling_std

        current_price = df[price_column_name].iloc[-1]
        dist_upper = (upper_band.iloc[-1] - current_price) / (2 * self.k_val * rolling_std.iloc[-1])
        dist_lower = (current_price - lower_band.iloc[-1]) / (2 * self.k_val * rolling_std.iloc[-1])

        self.bollinger_list.append({
            "peak": max(0, 100 * (1 - dist_upper)),
            "trough": max(0, 100 * (1 - dist_lower))
        })

        if len(self.bollinger_list) < 2:
            return float(self.bollinger_list[-1]["trough"]), float(self.bollinger_list[-1]["peak"])

        last_trough_probability = [round(float(i.get("trough", 0.0)), 2) for i in self.bollinger_list[-2:]]
        avg_trough_probability = (last_trough_probability[0] + last_trough_probability[1]) / 2
        last_peak_probability = [round(float(i.get("peak", 0.0)), 2) for i in self.bollinger_list[-2:]]
        avg_peak_probability = (last_peak_probability[0] + last_peak_probability[1]) / 2

        return float(avg_trough_probability), float(avg_peak_probability)

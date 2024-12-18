#!/bin/python3

# System lib
import os
import sys
import json
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
from config import get_strategy
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def get_stategy_handle(target):
    strategy_dict = get_strategy(target)
    strategy_type = strategy_dict['class']
    if strategy_type == 'basic':
        short = int(strategy_dict['short_window'])
        long = int(strategy_dict['long_window'])
        th = float(strategy_dict['threshold'])
        trade_interval = int(strategy_dict['cool_down_period'])
        stategy_handle = basic(short, long, th, trade_interval)
    elif strategy_type == 'xxxx':   # to be update
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
    #                 sum(short_df) * long_window_size - threshold * short_window_size * sum(long_df)
    # expect = x = -------------------------------------------------------------------------------------
    #                   threshold * short_window_size - long_window_size
    def mean_reversion_expect(self, df):
        df = self.mean_reversion(df)
        last_index = len(df) - 1
        if last_index - self.last_signal_day < self.trade_interval:
            return {}  # 仍在冷却期内

        short_df = df['Close'].tail(self.short - 1)
        long_df = df['Close'].tail(self.long - 1)
        last = df['Close'].tail(1).item()
        #log.get('backtest').info('last:%.2f'%(last))
        #log.get('backtest').info('threshold:%.2f'%(self.th))

        threshold = (1 - self.th)
        expect_buy = sum(short_df) * self.long - threshold * self.short * sum(long_df)
        expect_buy /= threshold * self.short - self.long
        #log.get('backtest').info('expect_buy:[0, %.2f]'%(expect_buy))
        
        threshold = (1 + self.th)
        expect_sell = sum(short_df) * self.long - threshold * self.short * sum(long_df)
        expect_sell /= threshold * self.short - self.long
        #log.get('backtest').info('expect_sell: [%.2f, +∞]'%(expect_sell))

        ret_dict = {}
        if expect_buy > 0 and abs((last - expect_buy) / last) < 0.1:         # expect > 0 or diff under 10%
            ret_dict.update({'buy':expect_buy})
        if expect_sell > 0 and abs((last - expect_sell) / last) < 0.1:       # expect > 0 or diff under 10%
            ret_dict.update({'sell':expect_sell})

        return ret_dict


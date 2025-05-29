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


def get_strategy_handle(target, trade_type):
    strategy_dict = get_strategy(target)
    strategy_type = strategy_dict[trade_type]['class']
    #log.get('backtest').info('get_strategy_handle:%s %s %s'%(target, strategy_type, str(strategy_dict)))
    stategy_handle = None
    if strategy_type == 'mean_reversion':
        stategy_handle = mean_reversion({
            'short': int(strategy_dict[trade_type]['detail']['short_window']),
            'window_size': int(strategy_dict[trade_type]['detail']['window_size']),
            'th': float(strategy_dict[trade_type]['detail']['threshold']),
            'trade_interval': int(strategy_dict[trade_type]['detail']['cool_down_period']),
        })
    elif strategy_type == 'bollinger':
        stategy_handle = bollinger({
            'window_size': int(strategy_dict[trade_type]['detail']['window_size']),
            'k_val': float(strategy_dict[trade_type]['detail']['k_val']),
            'probability_limit': float(strategy_dict[trade_type]['detail']['probability_limit']),
        })
    elif strategy_type == 'xxx':   # to be update
        pass
    return stategy_handle

def generate_strategy_list(strategy_type):
    if strategy_type == 'mean_reversion':
        short_range = range(2, 10+1)
        window_size_range = range(15, 40+1)
        th_range = range(1, 40+1)  # persentage / 10 (0.1% - 4%) step: 0.1%
        interval_range = range(1, 10+1)
        temp_list = []
        for a in th_range:
            for b in window_size_range:
                for c in short_range:
                    for d in interval_range:
                        temp_dict = {
                            'th' : float(a)/10,
                            'short' : int(c),
                            'window_size' : int(b),
                            'trade_interval' : int(d),
                        }
                        temp_list.append(mean_reversion(temp_dict))
        return temp_list
    elif strategy_type == 'bollinger':
        window_size_range = range(10, 80+1)
        probability_limit_range = range(65, 95+1)
        k_val_range = range(10, 70+1)  # persentage / 10 (1.0% - 7.0%) step: 0.1%
        interval_range = range(1, 10+1)
        temp_list = []
        for a in k_val_range:
            for b in window_size_range:
                for c in interval_range:
                    for d in probability_limit_range:
                        temp_dict = {
                            'k_val' : float(a)/10,
                            'probability_limit' : float(d),
                            'window_size' : int(b),
                            'trade_interval' : int(c),
                        }
                        temp_list.append(bollinger(temp_dict))
        return temp_list
    return []

'''
************************************  Rule  ************************************
1. Each strategy class, init to input parameters
    Such as "mean_reversion": short, window_size, th, trade_interval
2. Each strategy calculation factor's I/O data type
    input: DataFrame
    output: DataFrame with Signal column(Buy=1, Sell=-1, Hold=0)
********************************************************************************
'''

class mean_reversion:
    def __init__(self, config_dict):
        self.short = config_dict.get('short', 1)
        self.window_size = config_dict.get('window_size', 2)
        self.th = config_dict.get('th', 1.0) / 100
        self.trade_interval = config_dict.get('trade_interval', 1)

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
        last_signal_day = -self.trade_interval  # Start from the first day
        price_column_name = 'Price' if 'Price' in df.columns else \
            'Close' if 'Close' in df.columns else ''
        if price_column_name == '':
            return 0.1, 0.1
        # Calculate the window average
        df['Short_MA'] = df[price_column_name].rolling(window=self.short, min_periods=1).mean()
        df['Long_MA'] = df[price_column_name].rolling(window=self.window_size, min_periods=1).mean()
        df['Short_MA'] = pd.to_numeric(df['Short_MA'], errors='coerce')
        df['Long_MA'] = pd.to_numeric(df['Long_MA'], errors='coerce')

        df['Signal'] = 0
        for idx, row in df.iterrows():
            short_ma = row['Short_MA']
            long_ma = row['Long_MA']

            # if trade_interval has expired since the last operation
            if idx - last_signal_day >= self.trade_interval:
                # If the short window_avg is higher than window_size window_avg and the gap is greater than the threshold
                # Means that the short increase is large, and consider selling
                if (short_ma - long_ma)/short_ma > self.th:
                    df.loc[idx, 'Signal'] = -1
                    last_signal_day = idx

                # Contrary to above, short window_avg is lower than window_size window_avg
                elif (long_ma - short_ma)/long_ma > self.th:
                    df.loc[idx, 'Signal'] = 1
                    last_signal_day = idx

        short_df = df[price_column_name].tail(self.short - 1)
        long_df = df[price_column_name].tail(self.window_size - 1)
        if dog_id == None:
            last = df[price_column_name].tail(1).item()
        else:
            last = get_dog_last_price(dog_id)

        threshold = (1 - self.th)
        expect_buy = sum(short_df) * self.window_size - threshold * self.short * sum(long_df)
        expect_buy /= threshold * self.short - self.window_size
        
        threshold = (1 + self.th)
        expect_sell = sum(short_df) * self.window_size - threshold * self.short * sum(long_df)
        expect_sell /= threshold * self.short - self.window_size

        steepness = float(get_global_config('price_steepness'))
        # -700 to 700 near float corner case
        trough_probability = 100 * max(0.0, min(1.0, math.exp(max(-700, min(700, (-steepness * (last - expect_buy)))))))
        peak_probability =100 * max(0.0, min(1.0, math.exp(max(-700, min(700, (-steepness * (expect_sell - last)))))))

        return float(trough_probability), float(peak_probability)

class bollinger:
    def __init__(self, config_dict):
        self.window_size = config_dict.get('window_size', 10)
        self.k_val = config_dict.get('k_val', 1.0)
        self.probability_limit = config_dict.get('probability_limit', 90)
        self.trade_interval = config_dict.get('trade_interval', 1)

    def probability(self, df, dog_id=None, mean=True):
        price_column_name = 'Price' if 'Price' in df.columns else \
            'Close' if 'Close' in df.columns else ''
        if price_column_name == '':
            return 0.1, 0.1
        df['Mean'] = df[price_column_name].rolling(self.window_size).mean()
        df['Std'] = df[price_column_name].rolling(self.window_size).std()
        df['Upper_Band'] = df['Mean'] + self.k_val * df['Std']
        df['Lower_Band'] = df['Mean'] - self.k_val * df['Std']

        df['Peak'] = np.maximum(0, 100 * (1 - ((df['Upper_Band'] - df[price_column_name]) / (2 * self.k_val * df['Std']))))
        df['Trough'] = np.maximum(0, 100 * (1 - ((df[price_column_name] - df['Lower_Band']) / (2 * self.k_val * df['Std']))))

        bollinger_avg_cnt = int(get_global_config('bollinger_avg_cnt'))
        bollinger_avg_cnt = 1 if (bollinger_avg_cnt == 0) else bollinger_avg_cnt
        if mean:
            df['Peak_Mean'] = df['Peak'].rolling(bollinger_avg_cnt).mean()
            df['Trough_Mean'] = df['Trough'].rolling(bollinger_avg_cnt).mean()

        df['Signal'] = 0
        limit = float(get_global_config('bollinger_limit'))
        last_signal_day = -self.trade_interval

        for idx, row in df.iterrows():
            if mean:
                peak_mean = row['Peak_Mean']
                trough_mean = row['Trough_Mean']

            # if trade_interval has expired since the last operation
            if idx - last_signal_day >= self.trade_interval:
                if mean:
                    peak_triggered = (peak_mean > limit and trough_mean < limit)
                    trough_triggered = (peak_mean < limit and trough_mean > limit)
                else:
                    peak_triggered = df['Peak'].tail(bollinger_avg_cnt).gt(limit).all()
                    trough_triggered = df['Trough'].tail(bollinger_avg_cnt).gt(limit).all()

                if peak_triggered and not trough_triggered:
                    df.loc[idx, 'Signal'] = -1
                    last_signal_day = idx
                if not peak_triggered and trough_triggered:
                    df.loc[idx, 'Signal'] = 1
                    last_signal_day = idx
        if mean:
            return float(df['Trough_Mean'].tail(1).item()), float(df['Peak_Mean'].tail(1).item())
        else:
            return float(df['Trough'].tail(1).item()), float(df['Peak'].tail(1).item())

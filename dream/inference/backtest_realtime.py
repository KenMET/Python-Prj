#!/bin/python3

# System lib
import os
import sys
import time
import math
import argparse
import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.signal import argrelextrema

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
from strategy import bollinger, get_stategy_handle
sys.path.append(r'%s/../common'%(py_dir))
from config import get_global_config
from database import create_if_realtime_inexist, update_registered_time, get_registered_dog
from database import get_dog_realtime_min, get_dog_realtime_cnt, get_market_last
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def bollinger_band_probability(df, window=20, k=2):
    rolling_mean = df['Price'].rolling(window).mean()
    rolling_std = df['Price'].rolling(window).std()
    upper_band = rolling_mean + k * rolling_std
    lower_band = rolling_mean - k * rolling_std
    
    current_price = df['Price'].iloc[-1]
    dist_upper = (upper_band.iloc[-1] - current_price) / (2 * k * rolling_std.iloc[-1])
    dist_lower = (current_price - lower_band.iloc[-1]) / (2 * k * rolling_std.iloc[-1])
    
    return {
        "peak_prob": max(0, 100 * (1 - dist_upper)),
        "trough_prob": max(0, 100 * (1 - dist_lower))
    }

fee = 3
total_cash = 4000.0
order_list = []
min_earning = 10.0
earning = 0.0
opt_cash_limit = 1000
def opt(side, price, shares, time_str):
    global fee
    global total_cash
    global order_list
    global earning
    if side == 'Buy':
        total_buy = shares * price
        log.get().info('total_cash[%.2f], total_buy[%.2f]'%(total_cash, total_buy))
        if total_cash < total_buy:
            shares_tmp = total_cash // total_buy
            if shares_tmp == 0:
                #log.get().info('No enough monney[%.2f], Ignore1 %.2f[%d]'%(total_cash, shares_tmp, total_buy))
                return False
            total_buy = shares_tmp * price
            total_cash -= total_buy + fee
            if (shares / shares_tmp) >= 2:
                #log.get().info('No enough monney[%.2f], Ignore2 %.2f[%d]'%(total_cash, total_buy, shares_tmp))
                return False
            #log.get().info('No enough monney[%.2f], all in %.2f[%d]'%(total_cash, total_buy, shares_tmp))
        else:
            total_cash -= total_buy + fee
        order_list.append({
            'order_id': str(time.time()),
            'side':side,
            'price':price,
            'shares':shares,
        })
        return True
    elif side == 'Sell':
        order_index = -1
        for index in order_list:
            side_tmp = index['side']
            if side_tmp == side:
                continue
            shares = index['shares']
            price_cost = index['price']
            earning_tmp = (price - price_cost) * shares - fee
            if earning_tmp < min_earning:
                log.get().info('No enough Earning[%.2f] this time'%(earning_tmp))
                continue
            earning += earning_tmp
            total_cash += ((price * shares) - fee)
            log.get().info('[%s]Earning[%.2f] [%.2f -> %.2f](%d)'%(time_str, earning, price_cost, price, shares))
            order_index = order_list.index(index)
            break
        if order_index < 0:
            return False
        del order_list[order_index]
        return True


def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success...[%s]'%(py_name))
    
    if (args.last_min == '' or not args.last_min.isdigit()):
        log.get().error('Last Minutes Errot, please setup such as "--last_min 1440"')
        return
    last_min = int(args.last_min)

    if (args.target == ''):
        log.get().error('Target Null, please setup target such as "--target NVDA"')
        return
    else:
        df = pd.DataFrame(get_dog_realtime_min(args.target, last_min))
        df = df.sort_values(by='DogTime', ascending=True)
        #log.get().info(df)
        df['Time'] = pd.to_datetime(df['DogTime'].str.extract(r'(\d{8}\d{6})')[0], format='%Y%m%d%H%M%S')

        order_factor = 8
        max_indices = argrelextrema(df['Price'].values, np.greater, order=order_factor)
        local_maxima = df.iloc[max_indices[0]].copy()
        #log.get().info("Max:%s"%(str(local_maxima)))

        min_indices = argrelextrema(df['Price'].values, np.less, order=order_factor)
        local_minima = df.iloc[min_indices[0]].copy()
        #log.get().info("Min:%s"%(str(local_minima)))

        bollinger_limit = float(get_global_config('bollinger_limit'))
        stategy_handle = get_stategy_handle(args.target, 'short')
        continue_cnt = 2
        trough_list = [0.0, 0.0]
        peak_list = [0.0, 0.0]
        for i in range(stategy_handle.window_size, len(df)+1):
            subset = df.head(i)  # 或者使用 df.iloc[:i]
            #log.get().info(subset)
            last_data = subset.tail(1)
            last_data_price = float(last_data['Price'].iloc[0])
            trough, peak = stategy_handle.probability(subset)
            trough_list.append(trough)
            peak_list.append(peak)
            if trough > bollinger_limit and peak > bollinger_limit:
                log.get().warning('stategy might fault due to trough and  peak all > %.2f'%(bollinger_limit))
                continue

            if all(val > bollinger_limit for val in peak_list[-continue_cnt:]):
                log.get().info("[%s]Sell:%.2f (%.2f, %.2f)"%(args.target, last_data_price, trough, peak))
                flag = opt('Sell', last_data_price, 0, str(last_data['Time'].iloc[0]))
                peak_list = [0.0, 0.0]
            elif all(val > bollinger_limit for val in trough_list[-continue_cnt:]):
                log.get().info("[%s]Buy:%.2f (%.2f, %.2f)"%(args.target, last_data_price, trough, peak))
                shares = opt_cash_limit // last_data_price
                flag = opt('Buy', last_data_price, shares, None)
                trough_list = [0.0, 0.0]

        fig = go.Figure()
        # 价格线
        fig.add_trace(go.Scatter(x=df['Time'], y=df['Price'], mode='lines', name='Price'))

        # 成交量柱状图（加第二个 y 轴）
        fig.add_trace(go.Bar(x=df['Time'], y=df['Volume'], name='Volume', yaxis='y2', opacity=0.4))

        # 1. 价格线（主图）
        fig.add_trace(go.Scatter(
            x=df['Time'], 
            y=df['Price'], 
            mode='lines', 
            name='Price',
            line=dict(color='blue', width=2)
        ))

        # 2. 标记局部极大值（红色点）
        fig.add_trace(go.Scatter(
            x=local_maxima['Time'],
            y=local_maxima['Price'],
            mode='markers',
            name='Peak',
            marker=dict(color='red', size=8, symbol='triangle-up'),
            hovertemplate='<b>Peak</b>: %{y:.2f}<extra></extra>'
        ))

        # 3. 标记局部极小值（绿色点）
        fig.add_trace(go.Scatter(
            x=local_minima['Time'],
            y=local_minima['Price'],
            mode='markers',
            name='Trough',
            marker=dict(color='green', size=8, symbol='triangle-down'),
            hovertemplate='<b>Trough</b>: %{y:.2f}<extra></extra>'
        ))

        # 4. 成交量柱状图（次坐标轴）
        fig.add_trace(go.Bar(
            x=df['Time'],
            y=df['Volume'],
            name='Volume',
            yaxis='y2',
            opacity=0.4,
            marker=dict(color='grey')
        ))

        # 设置双 y 轴和布局
        fig.update_layout(
            title="Price & Volume with Extrema",
            xaxis=dict(title='Time'),
            yaxis=dict(title='Price', showgrid=True),
            yaxis2=dict(
                title='Volume',
                overlaying='y',
                side='right',
                showgrid=False  # 避免与主 y 轴网格重叠
            ),
            legend=dict(x=0.02, y=0.98),  # 调整图例位置
            height=500,
            hovermode='x unified'  # 鼠标悬停时显示所有数据
        )

        fig.write_html("stock_chart.html")

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")
    
    # Append arguments
    parser.add_argument('--last_min', type=str, default='', help='Back test since last X minutes, for example: 1440(1 day)')
    parser.add_argument('--target', type=str, default='', help='Backtest dog name')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)


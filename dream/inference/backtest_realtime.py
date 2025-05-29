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
from strategy import bollinger, get_strategy_handle
sys.path.append(r'%s/../common'%(py_dir))
from config import get_global_config, get_user_config
from other import append_dict_list, clear_dict_list, get_user_type
from database import create_if_realtime_inexist, update_registered_time, get_registered_dog
from database import get_dog_realtime_min, get_dog_realtime_cnt, get_market_last
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def init_prob_list():
    return [0.001 for i in range(int(get_global_config('bollinger_avg_cnt')))]

def get_continue_cnt(lst):
    if len(lst) == 0:
        return 1, 1
    count = 1
    last_element = lst[-1]
    for i in range(len(lst) - 2, -1, -1):
        if lst[i] == last_element:
            count += 1
        else:
            break
    if last_element == 'sell':
        return 1, count
    elif last_element == 'buy':
        return count, 1
    else:
        return 1, 1

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
        df = pd.DataFrame(get_dog_realtime_cnt(args.target, last_min))
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

        local_calcuma_buy = pd.DataFrame()
        local_calcuma_sell = pd.DataFrame()

        target = args.target
        trade_order_dict = {}
        prob_dict = {}
        trigger_price_dict = {}
        trigger_action_dict = {}

        user, q_type = get_user_type()
        avg_cnt = int(get_global_config('bollinger_avg_cnt'))
        opt_cash_limit = float(get_global_config('opt_cash_limit'))
        bollinger_limit = float(get_global_config('bollinger_limit'))
        min_diff = float(get_user_config(user, 'dog', 'min_percent'))
        profit_diff = float(get_user_config(user, 'dog', 'profit_percent'))

        fee = 3
        total_cash = 4000.0
        opt_cash_limit = 1000

        stategy_handle = get_stategy_handle(target, 'short')
        for i in range(stategy_handle.window_size, len(df)+1):
            subset = df.head(i)  # 或者使用 df.iloc[:i]
            #log.get().info(subset)

            trough_prob, peak_prob = stategy_handle.probability(subset)
            trough_prob_list = prob_dict.get(target, {}).get('trough', init_prob_list())
            peak_prob_list = prob_dict.get(target, {}).get('peak', init_prob_list())
            append_dict_list(prob_dict, target, trough_prob, key_sub='trough')
            append_dict_list(prob_dict, target, peak_prob, key_sub='peak')
            if trough_prob >= bollinger_limit and peak_prob >= bollinger_limit:
                log.get(log_name).error('%s: Probability Error both > %.2f [%.2f%% , %.2f%%]'%(target, bollinger_limit, trough_prob, peak_prob))
                break

            # Get continue action and increase avg_cnt as pyramid
            #buy_continue = 1
            #sell_continue = 1
            #avg_cnt = 1
            buy_continue, sell_continue = get_continue_cnt(trigger_action_dict.get(target, []))
            buy_avg_cnt = buy_continue * avg_cnt
            sell_avg_cnt = sell_continue * avg_cnt
            action_type = 'sell' if all(val > bollinger_limit for val in peak_prob_list[-sell_avg_cnt:]) else \
                        'buy' if all(val > bollinger_limit for val in trough_prob_list[-buy_avg_cnt:]) else ''

            # Get price of now
            last_data = subset.tail(1)
            now_price = float(last_data['Price'].iloc[0])
            #now_price = get_dog_last_price(target)
            #log.get().info('[%s][%s]:%.2f trough[%.2f], peak[%.2f], action[%s]'%(str(last_data['Time'].iloc[0]), target, now_price, trough_prob, peak_prob, action_type))
            last = trigger_price_dict.get(target, init_prob_list())[-1]     # using init_prob_list for init only, but store price data in fact

            # Get operation price threshold
            price_float_th = 0.01
            #price_float_th = float(get_global_config('price_float_th'))     # Reset to default every loop
            if action_type == 'sell':
                price_float_th *= sell_continue     # Ex: default_th=1.5%, Continue 3 times, then thrid time notify need have 4.5% deff
            elif action_type == 'buy':
                price_float_th *= buy_continue

            # Start submit order and update data and notify to phone
            if action_type != '':
                #log.get().debug('[%s] last[%.2f] now_price[%.2f]'%(target, last, now_price))
                price_diff = ((now_price - last) / last) if (action_type == 'sell') else ((last - now_price) / last)
                if last > 0.01 and price_diff < price_float_th:
                    log.get().debug('[%s]%s, too less diff last[%.2f], Now[%.2f] RequireDiff[%.2f%%]'%(target, 
                        action_type, last, now_price, price_float_th * 100))
                    continue
                append_dict_list(trigger_price_dict, target, now_price)
                append_dict_list(trigger_action_dict, target, action_type)

                if action_type == 'buy':
                    share = opt_cash_limit // now_price
                    total_buy = (share * now_price)
                    if total_cash < total_buy:
                        log.get().info('[%s] No enough cash, buy[%d][%.2f] total[%.2f]'%(target, share, now_price, total_buy))
                        continue
                    total_cash -= (total_buy + fee)
                    append_dict_list(trade_order_dict, target, {
                        'order_id': str(time.time()),
                        'price':now_price,
                        'shares':share,
                        'status':'New',
                    })
                    local_calcuma_buy = pd.concat([local_calcuma_buy, last_data])
                    log.get().info('[%s][%s] %s [%d] in %.2f'%(str(last_data['Time'].iloc[0]), 
                        target, action_type, share, now_price))
                else:
                    share = 0
                    earning = 0.0
                    order_list = trade_order_dict.get(target, [])
                    for index in order_list:
                        if index['status'] == 'New':
                            cost_price = index['price']
                            #if (now_price - cost_price) > 0:
                            if (((now_price - cost_price) / cost_price) * 100) > min_diff:
                                share += index['shares']
                                index['status'] = 'Filled'
                                earning += (((now_price - cost_price) * index['shares']) - fee)
                                #log.get().info('earning[%.2f] = now[%.2f] - cost[%.2f]'%(earning, now_price, cost_price))
                    if share != 0:
                        local_calcuma_sell = pd.concat([local_calcuma_sell, last_data])
                        log.get().info('[%s][%s] %s [%d] in %.2f, earning[%.2f]'%(str(last_data['Time'].iloc[0]), 
                            target, action_type, share, now_price, earning))

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
            line=dict(color='black', width=2)
        ))

        # 2. 标记局部极大值, 蓝色向下箭头
        fig.add_trace(go.Scatter(
            x=local_maxima['Time'],
            y=local_maxima['Price'],
            mode='markers',
            name='Peak',
            marker=dict(color='blue', size=8, symbol='triangle-down'),
            hovertemplate='<b>Peak</b>: %{y:.2f}<extra></extra>'
        ))

        # 2.5. 标记局部预测卖出点，向下箭头
        if len(local_calcuma_sell) != 0:
            fig.add_trace(go.Scatter(
                x=local_calcuma_sell['Time'],
                y=local_calcuma_sell['Price'],
                mode='markers',
                name='Sell',
                marker=dict(color='red', size=8, symbol='triangle-down'),
                hovertemplate='<b>Sell</b>: %{y:.2f}<extra></extra>'
            ))

        # 3. 标记局部极小值, 蓝色向下箭头
        fig.add_trace(go.Scatter(
            x=local_minima['Time'],
            y=local_minima['Price'],
            mode='markers',
            name='Trough',
            marker=dict(color='blue', size=8, symbol='triangle-up'),
            hovertemplate='<b>Trough</b>: %{y:.2f}<extra></extra>'
        ))

        # 3.5. 标记局部预测买入点，黄色向上箭头
        if len(local_calcuma_buy) != 0:
            fig.add_trace(go.Scatter(
                x=local_calcuma_buy['Time'],
                y=local_calcuma_buy['Price'],
                mode='markers',
                name='Buy',
                marker=dict(color='green', size=8, symbol='triangle-up'),
                hovertemplate='<b>Buy</b>: %{y:.2f}<extra></extra>'
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
            legend=dict(x=1.05, y=0.5),  # 调整图例位置
            height=500,
            hovermode='x unified'  # 鼠标悬停时显示所有数据
        )

        fig.write_html("stock_chart.html")


def get_realtime_filter_df(target, minutes):
    # Fetch dog realtime market info
    df = pd.DataFrame(get_dog_realtime_min(target, last_min=minutes))
    if 'DogTime' not in df.columns:
        return pd.DataFrame()
    #log.get(log_name).info(df)
    df = df.sort_values(by='DogTime', ascending=True)
    df['Time'] = pd.to_datetime(df['DogTime'].str.extract(r'(\d{8}\d{6})')[0], format='%Y%m%d%H%M%S')

    # Filter for time range
    df['Time_only'] = df['Time'].dt.time
    #start_time = pd.to_datetime('16:00:00').time()
    #end_time = pd.to_datetime('02:00:00').time()
    #filtered_df = df[((df['Time_only'] >= start_time)|(df['Time_only'] <= end_time))]
    #return filtered_df
    return df

def test():
    target = 'NVDL'
    stategy_handle = get_strategy_handle(target, 'short')
    df = get_realtime_filter_df(target, int(stategy_handle.window_size * 3))     # Must large then window size
    trough_prob, peak_prob = stategy_handle.probability(df, dog_id=target)
    print (trough_prob, peak_prob)

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")
    
    # Append arguments
    parser.add_argument('--last_min', type=str, default='', help='Back test since last X minutes, for example: 1440(1 day)')
    parser.add_argument('--target', type=str, default='', help='Backtest dog name')
    
    # 解析命令行参数
    args = parser.parse_args()
    #main(args)
    test()

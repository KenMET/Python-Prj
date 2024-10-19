#!/bin/python3

# System lib
import os
import sys
import json
import random
import hashlib
import argparse
import datetime, time
import numpy as np
import pandas as pd
from decimal import Decimal

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
import adata
import akshare as ak
import longport.openapi
from strategy import get_strategy, basic
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_dream_dog as dbdd
import db_dream_dog_info as dbddi
import db_dream_secret as dbds
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/xml_operator'%(py_dir))
import xml_operator as xo
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log


def get_market_by_range(target, start, end):
    db = dbdd.db('dream_dog')
    ret = db.query_dog_markey_by_daterange(target, start, end)
    df = pd.DataFrame([db.get_dict_from_obj(i) for i in ret])
    
    # Make sure date soted
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')           # 确保 Close 列为数值类型

    return df

def get_portfolio(df):
    # 初始资金和参数
    capital = 10000.0   # 初始化资金
    
    shares = 0  # 初始化持仓
    transaction_fee = 5  # 每次交易的手续费
    total_capital = capital

    # 设置参数
    threshold = 0.5  # 信号触发的阈值
    cool_down_period = 5  # 冷却期为5天
    last_signal_day = -cool_down_period  # 初始化最近的信号发生时间为负值

    for i in range(len(df)):
        current_price = df['Close'].iloc[i]

        # 在每个时间点计算持仓的市场价值
        if shares > 0:
            total_capital = shares * current_price + capital  # 添加持仓的市场价值

        # 买入逻辑
        if df['Position'].iloc[i] > 0.9 and df['Signal'].iloc[i] == 1:  # 买入信号
            if shares > 0:  # 如果已有持仓
                cost = shares * current_price  # 计算目前持仓市值
                additional_shares = min(shares, (capital - transaction_fee) // current_price)  # 买入同等数量的股票，或余额不足时全仓买入
            else:  # 如果没有持仓
                additional_shares = 5  # 底仓买入5股

            if additional_shares > 0:  # 确保能买入
                diff = additional_shares * current_price + transaction_fee  # 扣除买入金额和手续费
                capital -= diff
                shares += additional_shares  # 更新持仓
                log.get(py_name).info('Buy:%s, value:%.3f qty:%d(%0.3f) hold:%d cap:%.3f'%(df['Date'].iloc[i].date(), 
                    current_price, additional_shares, diff, shares, total_capital))

        # 卖出逻辑
        elif df['Position'].iloc[i] < -0.9 and df['Signal'].iloc[i] == -1:  # 卖出信号
            if shares > 1:  # 如果持有多于1股
                sell_shares = shares // 2  # 卖出50%持仓
            else:  # 如果只剩1股
                sell_shares = shares  # 清仓

            if sell_shares > 0:  # 确保能卖出
                diff = sell_shares * current_price - transaction_fee    # 增加卖出金额，扣除手续费
                capital += diff
                shares -= sell_shares  # 更新持仓
                log.get(py_name).info('Sell:%s, value:%.3f qty:%d(%0.3f) hold:%d cap:%.3f'%(df['Date'].iloc[i].date(), 
                    current_price, sell_shares, diff, shares, total_capital))

    return total_capital

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

def backtest(target, df):
    stategy_handle = get_stategy_handle(target)
    if stategy_handle == None:
        log.get(py_name).error('stategy_handle Null')
        return

    df = stategy_handle.mean_reversion(df)
    # Output the data of the trading signal
    trades = df[df['Signal'] != 0]
    log.get(py_name).info(trades)

    final_capital = get_portfolio(df)
    log.get(py_name).info('Final capital:%.3f'%(final_capital))

def pridct_next(target, df):
    stategy_handle = get_stategy_handle(target)
    if stategy_handle == None:
        log.get(py_name).error('stategy_handle Null')
        return

    next_predict = stategy_handle.mean_reversion_expect(df)
    log.get(py_name).info(next_predict)

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get(py_name).info('Logger Creat Success...[%s]'%(py_name))
    
    if (args.target == ''):
        log.get(py_name).error('Target Null, please setup target by "--target XXX"')
        return
    if (args.start == ''):
        log.get(py_name).error('Start Date Null, please setup start date "--start 20240101"')
        return
    end_date = datetime.date.today()
    if (args.end != ''):
        end_date = datetime.datetime.strptime(args.end, "%Y%m%d").date()
    start_date = datetime.datetime.strptime(args.start, "%Y%m%d").date()

    if ((end_date - start_date).days < 30):
        log.get(py_name).error('Start day too fucking less, set "start" to a date before 1 fucking month')
        return

    df = get_market_by_range(args.target, start_date, end_date)
    backtest(args.target, df)
    #pridct_next(args.target, df)
    

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")
    
    # Append arguments
    parser.add_argument('--start', type=str, default='', help='Start Date, for example: 20241001')
    parser.add_argument('--end', type=str, default='', help='End Date, null as today')
    parser.add_argument('--target', type=str, default='', help='Backtest dog name')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)


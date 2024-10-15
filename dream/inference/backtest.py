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

    return df

def get_portfolio(df):
    # 初始资金和参数
    capital = 10000.0   # 初始化资金
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')           # 确保 Close 列为数值类型
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

    # 输出最终的投资组合价值
    log.get(py_name).info('Final capital:%.3f'%(total_capital))

def backtest(df):
    # 设置参数
    short_window = 5
    long_window = 20
    threshold = 5  # 信号触发的阈值, 百分比
    cool_down_period = 2  # 冷却期, 天
    last_signal_day = -cool_down_period  # 初始化最近的信号发生时间为负值

    # 计算移动平均线
    df['Short_MA'] = df['Close'].rolling(window=short_window, min_periods=1).mean()
    df['Long_MA'] = df['Close'].rolling(window=long_window, min_periods=1).mean()

    # 初始化信号列（买入=1，卖出=-1，持仓=0）
    df['Signal'] = 0

    # 当短期均线上穿长期均线时，发出买入信号
    #df.loc[short_window:, 'Signal'] = np.where(df['Short_MA'][short_window:] > df['Long_MA'][short_window:], 1, 0)
    # 卖出信号：短期均线向下穿过长期均线
    #df.loc[short_window:, 'Signal'] = np.where(df['Short_MA'][short_window:] < df['Long_MA'][short_window:], -1, df['Signal'][short_window:])
    # 启用 阈值和冷却期 ，不然很容易产生频繁交易
    for i in range(len(df)):
        short_ma = df['Short_MA'].iloc[i]
        long_ma = df['Long_MA'].iloc[i]

        # 距离上一次操作是否超过冷却期
        if i - last_signal_day >= cool_down_period:
            # 如果短期均线比长期均线高，并且差距大于阈值，则生成卖出信号
            if (short_ma - long_ma)/short_ma > (threshold/100):
                df.loc[i, 'Signal'] = -1  # 卖出信号
                last_signal_day = i  # 更新最近的信号时间

            # 如果短期均线比长期均线低，并且差距大于阈值，则生成买入信号
            elif (long_ma - short_ma)/long_ma > (threshold/100):
                df.loc[i, 'Signal'] = 1  # 买入信号
                last_signal_day = i  # 更新最近的信号时间
        else:
            df.loc[i, 'Signal'] = 0  # 在冷却期内不产生信号

    # 生成买入/卖出的实际交易信号， 防止一个信号在一段时间内重复交易的
    df['Position'] = df['Signal'].diff()

    # 输出交易信号的数据
    trades = df[df['Signal'] != 0]
    log.get(py_name).info(trades)
    
    return df

def main(args):
    log.init(py_dir, py_name, log_mode='w', log_level='info', console_enable=True)
    log.get(py_name).info('Logger Creat Success...')
    
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
    
    df = backtest(df)
    get_portfolio(df)

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


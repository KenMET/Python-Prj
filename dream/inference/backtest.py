#!/bin/python3

# System lib
import os
import sys
import math
import argparse
import datetime

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
from strategy import basic, get_strategy_handle, generate_basic_strategy_list
sys.path.append(r'%s/../common'%(py_dir))
from config import get_dog, get_global_config
from database import get_market_by_range
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

init_capital = 10000.0
init_transaction_fee = 5  # 每次交易的手续费

'''
def get_portfolio(df):
    # 初始资金和参数
    capital = init_capital   # 初始化资金
    
    shares = 0  # 初始化持仓
    transaction_fee = init_transaction_fee  # 每次交易的手续费
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
                #log.get().info('Buy:%s, value:%.3f qty:%d(%0.3f) hold:%d cap:%.3f'%(df['Date'].iloc[i].date(), 
                #    current_price, additional_shares, diff, shares, total_capital))

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
                #log.get().info('Sell:%s, value:%.3f qty:%d(%0.3f) hold:%d cap:%.3f'%(df['Date'].iloc[i].date(), 
                #    current_price, sell_shares, diff, shares, total_capital))

    return total_capital

def backtest_single(target, df):
    stategy_handle = get_strategy_handle(target, 'long')
    if stategy_handle == None:
        log.get().error('stategy_handle Null')
        return init_capital

    df = stategy_handle.mean_reversion(df)
    # Output the data of the trading signal
    trades = df[df['Signal'] != 0]
    #log.get().info(trades)

    strategy_dict = {
        'th' : stategy_handle.th,
        'long' : stategy_handle.long,
        'short' : stategy_handle.short,
        'trade_interval' : stategy_handle.trade_interval,
    }
    final_capital = get_portfolio(df)
    capital_per = ((final_capital-init_capital)/init_capital ) * 100
    log.get().info('[%.2f -> %.2f](%.2f%%) %s'%(init_capital, final_capital, capital_per, strategy_dict))

    return final_capital

def backtest_traversal_strategy(target, df):
    stategy_list = generate_basic_strategy_list()
    stategy_handle = None
    max_capital = 0
    for index in stategy_list:
        stategy_handle = basic(index['short'], index['long'], index['th'], index['trade_interval'])
        if stategy_handle == None:
            log.get().error('stategy_handle Null')
            return
        df = stategy_handle.mean_reversion(df)
        # Output the data of the trading signal
        trades = df[df['Signal'] != 0]
        final_capital = get_portfolio(df)

        if final_capital > max_capital:
            max_capital = final_capital
            capital_per = ((final_capital-init_capital)/init_capital ) * 100
            log.get().info('[%.2f -> %.2f](%.2f%%) %s'%(init_capital, final_capital, capital_per, index))

def backtest_traversal_dog(start_date, end_date):
    short = 6
    long = 30
    th = 1.0
    trade_interval = 3
    # US 70% WIN AVG: th: 1.0  long: 21    short: 8    trade_interval:3
    # US 80% WIN AVG: th: 1.0  long: 30    short: 6    trade_interval:3

    winning_cnt = 0
    cn_dog_list = get_dog('cn')
    us_dog_list = get_dog('us')
    temp_list = []
    #temp_list = list(set(temp_list).union(cn_dog_list))
    temp_list = list(set(temp_list).union(us_dog_list))
    for dog_index in temp_list:
        stategy_handle = basic(short, long, th, trade_interval)
        df = get_market_by_range(dog_index, start_date, end_date)
        df = stategy_handle.mean_reversion(df)
        trades = df[df['Signal'] != 0]
        final_capital = get_portfolio(df)
        capital_per = ((final_capital-init_capital)/init_capital ) * 100
        if capital_per > 5:    # over 5%
            winning_cnt += 1
            log.get().info('[%s] [%.2f -> %.2f](%.2f%%)'%(dog_index, init_capital, final_capital, capital_per))
        else:
            log.get().info('[%s] [%.2f -> %.2f](%.2f%%)'%(dog_index, init_capital, final_capital, capital_per))
        df = df.drop(df.index)

    per = (winning_cnt / len(temp_list)) * 100
    log.get().info('[%s] Win[%.2f%%](%d/%d)'%(dog_index, per, winning_cnt, len(temp_list)))

def backtest_winning_per(start_date, end_date):
    stategy_list = generate_basic_strategy_list()
    max_per = 0
    for index in stategy_list:
        winning_cnt = 0
        cn_dog_list = get_dog('cn')
        us_dog_list = get_dog('us')
        temp_list = []
        #temp_list = list(set(temp_list).union(cn_dog_list))
        temp_list = list(set(temp_list).union(us_dog_list))
        for dog_index in temp_list:
            df = get_market_by_range(dog_index, start_date, end_date)
            stategy_handle = basic(index['short'], index['long'], index['th'], index['trade_interval'])
            df = stategy_handle.mean_reversion(df)
            trades = df[df['Signal'] != 0]
            final_capital = get_portfolio(df)
            if (final_capital-init_capital)/init_capital > 0.05:    # over 5%
                winning_cnt += 1
        per = (winning_cnt / len(temp_list)) * 100
        if per > max_per:
            max_per = per
            log.get().info('Win[%.2f%%](%d/%d) Detect MAX for %s'%(per, winning_cnt, len(temp_list), str(index)))
        else:
            log.get().info('Win[%.2f%%](%d/%d) Not good for %s'%(per, winning_cnt, len(temp_list), str(index)))
'''

def get_portfolio(df, strategy_handle):
    capital = init_capital   # 初始化资金
    
    shares = 0  # 初始化持仓
    transaction_fee = init_transaction_fee  # 每次交易的手续费
    total_capital = capital

    filtered_df = df[df['Signal'] != 0]
    for idx, row in filtered_df.iterrows():
        calcu_df = df.iloc[max(0, idx - strategy_handle.long * 2 + 2) : (idx + 1)]
        trough_prob, peak_prob = strategy_handle.probability(calcu_df, reload_reversion=False)
        #log.get().info('[%s]Expect: [0, %.2f] [%.2f, +∞]'%(row['Date'].date(), trough_prob, peak_prob))

        current_price = df['Close'].iloc[idx]

        # 在每个时间点计算持仓的市场价值
        if shares > 0:
            total_capital = shares * current_price + capital  # 添加持仓的市场价值

        # 买入逻辑
        if trough_prob > 80 and peak_prob < 20:  # 买入信号
            if shares > 0:  # 如果已有持仓
                cost = shares * current_price  # 计算目前持仓市值
                additional_shares = min(shares, (capital - transaction_fee) // current_price)  # 买入同等数量的股票，或余额不足时全仓买入
            else:  # 如果没有持仓
                additional_shares = 5  # 底仓买入5股

            if additional_shares > 0:  # 确保能买入
                diff = additional_shares * current_price + transaction_fee  # 扣除买入金额和手续费
                capital -= diff
                shares += additional_shares  # 更新持仓
                #log.get().info('Buy:%s, value:%.3f qty:%d(%0.3f) hold:%d cap:%.3f'%(df['Date'].iloc[idx].date(), 
                #    current_price, additional_shares, diff, shares, total_capital))

        # 卖出逻辑
        elif peak_prob > 80 and trough_prob < 20:  # 卖出信号
            if shares > 1:  # 如果持有多于1股
                sell_shares = shares // 2  # 卖出50%持仓
            else:  # 如果只剩1股
                sell_shares = shares  # 清仓

            if sell_shares > 0:  # 确保能卖出
                diff = sell_shares * current_price - transaction_fee    # 增加卖出金额，扣除手续费
                capital += diff
                shares -= sell_shares  # 更新持仓
                #log.get().info('Sell:%s, value:%.3f qty:%d(%0.3f) hold:%d cap:%.3f'%(df['Date'].iloc[idx].date(), 
                #    current_price, sell_shares, diff, shares, total_capital))

    return total_capital


def specific_strategy_specific_dog(target_list, start_date, end_date):
    if len(target_list) != 1:
        log.get().error('Test mode is "specific_strategy_specific_dog", target_list length must be 1...')
        return init_capital
    target = target_list[0]
    strategy_handle = get_strategy_handle(target, 'long')
    if strategy_handle == None:
        log.get().error('strategy_handle Null')
        return init_capital
    #strategy_handle.short = 3
    #strategy_handle.long = 15
    #strategy_handle.th = 5 / 100     # 5%
    #strategy_handle.trade_interval = 2

    df = get_market_by_range(target, start_date, end_date)
    if len(df) < strategy_handle.long:
        log.get().error('Data too less: [%s] [%s -> %s]'%(target, str(start_date), str(end_date)))
        return init_capital

    df = strategy_handle.mean_reversion(df)
    final_capital = get_portfolio(df, strategy_handle)
    capital_per = ((final_capital-init_capital)/init_capital ) * 100
    strategy_dict = {
        'th' : strategy_handle.th, 'long' : strategy_handle.long,
        'short' : strategy_handle.short, 'trade_interval' : strategy_handle.trade_interval,
    }
    log.get().info('[%.2f -> %.2f](%.2f%%) %s'%(init_capital, final_capital, capital_per, strategy_dict))

    return final_capital

def all_strategy_specific_dog(target_list, start_date, end_date):
    if len(target_list) != 1:
        log.get().error('Test mode is "specific_strategy_specific_dog", target_list length must be 1...')
        return init_capital
    target = target_list[0]
    strategy_list = generate_basic_strategy_list()
    strategy_handle = None
    max_capital = 0

    df = get_market_by_range(target, start_date, end_date)
    for index in strategy_list:
        strategy_handle = basic(index['short'], index['long'], index['th'], index['trade_interval'])
        if strategy_handle == None:
            log.get().error('strategy_handle Null')
            return
        if len(df) < strategy_handle.long:
            log.get().error('Data too less: [%s] [%s -> %s]'%(target, str(start_date), str(end_date)))
            return init_capital

        df = strategy_handle.mean_reversion(df)
        final_capital = get_portfolio(df, strategy_handle)
        if final_capital > max_capital:
            max_capital = final_capital
            capital_per = ((final_capital-init_capital)/init_capital ) * 100
            log.get().info('[%.2f -> %.2f](%.2f%%) %s'%(init_capital, final_capital, capital_per, index))

def specific_strategy_all_dog(target_list, start_date, end_date):
    pass
def all_strategy_all_dog(target_list, start_date, end_date):
    pass

tmp_cb_dict = {
    'specific_strategy_specific_dog': specific_strategy_specific_dog,
    'all_strategy_specific_dog': all_strategy_specific_dog,
    'specific_strategy_all_dog': specific_strategy_all_dog,
    'all_strategy_all_dog': all_strategy_all_dog,
}

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success...[%s]'%(py_name))
    
    if (args.start == ''):
        log.get().error('Start Date Null, please setup start date "--start 20240101"')
        return
    end_date = datetime.date.today()
    if (args.end != ''):
        end_date = datetime.datetime.strptime(args.end, "%Y%m%d").date()
    start_date = datetime.datetime.strptime(args.start, "%Y%m%d").date()

    if ((end_date - start_date).days < 30):
        log.get().error('Start day too fucking less, set "start" to a date before 1 fucking month')
        return

    #test_mode = 'specific_strategy_specific_dog'
    test_mode = 'all_strategy_specific_dog'
    #test_mode = 'specific_strategy_all_dog'
    #test_mode = 'all_strategy_all_dog'
    cb = tmp_cb_dict.get(test_mode, None)
    if cb == None:
        log.get().error('Test mode not found...')
        return
    target_list = []
    target_list.append(args.target)
    cb(target_list, start_date, end_date)

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


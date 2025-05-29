#!/bin/python3

# System lib
import os
import sys
import math
import time
import argparse
import datetime
import threading
import multiprocessing

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
from strategy import get_strategy_handle, generate_strategy_list
sys.path.append(r'%s/../common'%(py_dir))
from config import get_dog, get_global_config
from database import get_market_by_range
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

init_capital = 10000.0
init_transaction_fee = 5  # 每次交易的手续费

def get_portfolio(df, window_size):
    capital = init_capital   # 初始化资金

    shares = 0  # 初始化持仓
    transaction_fee = init_transaction_fee  # 每次交易的手续费
    total_capital = capital

    filtered_df = df[df['Signal'] != 0]
    for idx, row in filtered_df.iterrows():
        calcu_df = df.iloc[max(0, idx - window_size * 2 + 2) : (idx + 1)]

        current_price = df['Close'].iloc[idx]

        # 在每个时间点计算持仓的市场价值
        if shares > 0:
            total_capital = shares * current_price + capital  # 添加持仓的市场价值

        if row['Signal'] == 1:  # 买入信号
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

        if row['Signal'] == -1:  # 卖出信号
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

def walk_single(target_list, start_date, end_date, strategy=None):
    if len(target_list) == 0:
        log.get().error('Target List None...')
        return init_capital
    final_capital_dict = {}
    for target in target_list:
        strategy_handle = get_strategy_handle(target, 'long')
        if strategy_handle == None:
            log.get().error('strategy_handle None')
            return init_capital 

        window_size = strategy_handle.window_size
        strategy_dict = {}
        members = [attr for attr in dir(strategy_handle) if not callable(getattr(strategy_handle, attr)) and not attr.startswith('__')]
        for member in members:
            strategy_dict.update({member:getattr(strategy_handle, member)})

        df = get_market_by_range(target, start_date, end_date)
        if len(df) < window_size:
            log.get().error('Data too less: [%s] [%s -> %s]'%(target, str(start_date), str(end_date)))
            return init_capital

        trough, peak = strategy_handle.probability(df)
        final_capital = get_portfolio(df, window_size)

        capital_per = ((final_capital-init_capital)/init_capital ) * 100
        final_capital_dict.update({target:{'final_capital':final_capital, 'capital_per':capital_per, 'strategy':strategy_dict}})
        log.get().info('[%s][%.2f -> %.2f](%.2f%%) %s'%(target, init_capital, final_capital, capital_per, strategy_dict))

    if len(final_capital_dict) > 1:
        success_cnt = 0
        for target in final_capital_dict:
            capital_per = final_capital_dict[target]['capital_per']
            if capital_per < 5.0 and capital_per > -5.0:
                continue
            if capital_per > 5.0:
                success_cnt += 1
        log.get().info('Winning Rate: %.2f%% in default'%(100*success_cnt/len(final_capital_dict)))

def walk_dog(target_list, start_date, end_date, strategy='mean_reversion'):
    if len(target_list) == 0:
        log.get().error('Target List None...')
        return init_capital
    final_capital_dict = {}

    THREAD_LIMIT = 20
    semaphore = threading.Semaphore(THREAD_LIMIT)
    lock = threading.Lock()
    def process_strategy(target, strategy_handle, df):
        nonlocal max_capital
        trough, peak = strategy_handle.probability(df)
        final_capital = get_portfolio(df, strategy_handle.window_size)
        with lock:
            if final_capital > max_capital:
                max_capital = final_capital
                capital_per = ((final_capital-init_capital)/init_capital ) * 100
                strategy_dict = {}
                members = [attr for attr in dir(strategy_handle) if not callable(getattr(strategy_handle, attr)) and not attr.startswith('__')]
                for member in members:
                    strategy_dict.update({member:getattr(strategy_handle, member)})
                log.get('backtest').info('[%s][%.2f -> %.2f](%.2f%%) %s'%(target, init_capital, final_capital, capital_per, strategy_dict))
        semaphore.release()

    for target in target_list:
        max_capital = 0.0
        df = get_market_by_range(target, start_date, end_date)
        strategy_list = generate_strategy_list(strategy)
        threads = []
        for strategy_handle in strategy_list:
            if strategy_handle == None:
                log.get().error('strategy_handle None')
                return init_capital 
            if len(df) < strategy_handle.window_size:
                log.get().error('Data too less: [%s] [%s -> %s]'%(target, str(start_date), str(end_date)))
                return init_capital
            semaphore.acquire()
            thread = threading.Thread(target=process_strategy, args=(target, strategy_handle, df.copy(), ))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

def walk_strategy(target_list, start_date, end_date, strategy='mean_reversion'):
    if len(target_list) == 0:
        log.get().error('Target List None...')
        return init_capital
    winning_dict = {}
    max_success_cnt = 0

    THREAD_LIMIT = 20
    semaphore = threading.Semaphore(THREAD_LIMIT)
    lock = threading.Lock()
    def process_strategy(target, strategy_handle, df):
        nonlocal winning_dict
        trough, peak = strategy_handle.probability(df)
        final_capital = get_portfolio(df, strategy_handle.window_size)
        with lock:
            capital_per = ((final_capital-init_capital)/init_capital ) * 100
            winning_dict.update({target:{'final_capital':final_capital, 'capital_per':capital_per}})
            #log.get('backtest').info('[%s][%.2f -> %.2f](%.2f%%)'%(target, init_capital, final_capital, capital_per))
        semaphore.release()

    df_dict = {}
    for target in target_list: 
        df_dict.update({target:get_market_by_range(target, start_date, end_date)})

    strategy_list = generate_strategy_list(strategy)
    for strategy_handle in strategy_list:
        success_cnt = 0
        threads = []
        if strategy_handle == None:
            log.get().error('strategy_handle None')
            return init_capital 
        for target in target_list:
            df = df_dict.get(target)
            if len(df) < strategy_handle.window_size:
                log.get('backtest').error('Data too less: [%s] [%s -> %s]'%(target, str(start_date), str(end_date)))
                return init_capital
            semaphore.acquire()
            thread = threading.Thread(target=process_strategy, args=(target, strategy_handle, df.copy(), ))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

        for target in winning_dict:
            capital_per = winning_dict[target]['capital_per']
            if capital_per < 5.0 and capital_per > -5.0:
                continue
            if capital_per > 5.0:
                success_cnt += 1
        if success_cnt > max_success_cnt:
            max_success_cnt = success_cnt
        strategy_dict = {}
        members = [attr for attr in dir(strategy_handle) if not callable(getattr(strategy_handle, attr)) and not attr.startswith('__')]
        for member in members:
            strategy_dict.update({member:getattr(strategy_handle, member)})
        log.get().info('Winning Rate: %.2f%% in %s'%(100*success_cnt/len(winning_dict), str(strategy_dict)))

tmp_cb_dict = {
    'walk_dog': walk_dog,
    'walk_single': walk_single,
    'walk_strategy': walk_strategy,
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

    cb = tmp_cb_dict.get(args.mode, None)
    if cb == None:
        log.get().error('Test mode not found...')
        return
    target_list = []
    if args.target == '':
        cn_dog_list = get_dog('cn')
        #target_list += cn_dog_list         # append CN dog
        us_dog_list = get_dog('us')
        target_list += us_dog_list          # append US dog
    else:
        target_list.append(args.target)
    log.get().info('Start backtest for %s'%(str(target_list)))
    cb(target_list, start_date, end_date, args.strategy)

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    parser.add_argument('--start', type=str, default='', help='Start Date, for example: 20241001')
    parser.add_argument('--end', type=str, default='', help='End Date, null as today')
    parser.add_argument('--target', type=str, default='', help='Backtest dog name')
    parser.add_argument('--strategy', type=str, default='mean_reversion', help='Backtest dog strategy')
    parser.add_argument('--mode', type=str, default='walk_single', help='Backtest mode(walk_single/walk_dog/walk_strategy)')

    # For Example:
    # 1. I need backtest the specific dog with sprcific strategy (strategy from config)
    #       python3 backtest.py --target NVDA --start 20240101 --mode walk_single
    # 2. I need backtest the specific strategy with all dogs (strategy from config)
    #       python3 backtest.py --start 20240101 --mode walk_single
    # 3. I need backtest the specific dog with walking all strategy (strategy from genrerated)
    #       python3 backtest.py --target NVDA --start 20240101 --mode walk_dog --strategy bollinger
    # 4. I need backtest all strategy with all dog to get the winning rate (strategy from genrerated)
    #       python3 backtest.py --start 20240101 --mode walk_strategy --strategy mean_reversion
    
    args = parser.parse_args()
    main(args)


#!/bin/python3

# System lib
import os
import sys
import math
import time
import random
import threading
import multiprocessing

import pandas as pd

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../common'%(py_dir))
from config import get_global_config, get_short_trade_list
from other import get_user_type, get_next_inject, get_prev_inject, retry_func
from other import get_current_session_and_remaining_time, append_dict_list, clear_dict_list
from sock_order import submit_order, query_order, cancel_order, modify_order
from sock_realtime import register_dog
sys.path.append(r'%s/../input'%(py_dir))
from longport_api import quantitative_init
from database import get_house_detail, get_last_price_from_db, get_dog_realtime_min
sys.path.append(r'%s/../inference'%(py_dir))
from strategy import get_strategy_handle
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

log_name = None
def get_name():
    global log_name
    return log_name
def set_name(name):
    global log_name
    log_name = name


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

def short_term_trade(house_dict):
    def init_prob_list():
        return [0.001 for i in range(int(get_global_config('bollinger_avg_cnt')))]
    def get_holding_by_dog_id(holding_dict, dog_id):
        for index in holding_dict:
            if index.get('Code', '').find(dog_id+'.') >= 0:
                return index
        return {}

    # Register dog to realtime service
    user_type = get_user_type('-')
    user = user_type.split('-')[0]
    trade_list = get_short_trade_list(user)
    try:
        for index in trade_list:
            recv_dict = register_dog(index)
            log.get(get_name()).info('[short_term_trade]register realtime for: %s %s'%(index, str(recv_dict)))
    except Exception as e:
        log.get(get_name()).error('Exception captured in short_term_trade register_dog: %s'%(str(e)))

    # Get target list and global static parameters
    target_list = random.sample(trade_list, 2)
    log.get(get_name()).info('random choice target_list: %s'%(str(target_list)))
    available_cash = float(house_dict['AvailableCash'])
    avg_cnt = int(get_global_config('bollinger_avg_cnt'))
    opt_cash_limit = float(get_global_config('opt_cash_limit'))
    bollinger_limit = float(get_global_config('bollinger_limit'))

    # Init data or object
    trade_order_dict = {}
    prob_dict = {}
    trigger_price_dict = {}
    trigger_action_dict = {}

    log.get(get_name()).info('Starting loop...')
    while(True):
        time.sleep(int(get_global_config('realtime_interval')))
        error_cnt = 0

        # Check current session
        try:
            now_seesion, surplus_min = get_current_session_and_remaining_time('Post')   # Track till Post session end
            if now_seesion == 'Night' or surplus_min < 30:
                log.get(get_name()).info('Current Session: %s, [%d] minutes left, stop short trade monitor...'%(now_seesion, surplus_min))
                break
            else:
                log.get(get_name()).debug('Current Session: %s, [%d] minutes left, continue short trade monitor...'%(now_seesion, surplus_min))
        except Exception as e:
            log.get(get_name()).error('Exception captured in get_current_session_and_remaining_time: %s'%(str(e)))
            time.sleep(10)
            continue

        content = ''
        for target in trade_list:
            stategy_handle = get_strategy_handle(target, 'short')

            # Get and update probability
            #start_time = time.time()
            try:
                df = get_realtime_filter_df(target, int(stategy_handle.window_size * 2))     # Must large then window size
            except Exception as e:
                log.get(get_name()).error('Exception captured in get_realtime_filter_df[%s]: %s'%(target, str(e)))
                time.sleep(10)
                continue
            if len(df) == 0:
                log.get(get_name()).error('%s Nothing in df'%(target))
                error_cnt += 1
                continue
            #log.get(get_name()).debug('get_realtime_filter_df elapsed_time: %.3f'%(time.time() - start_time))    # Read database cost time
            trough_prob, peak_prob = stategy_handle.probability(df, dog_id=target, mean=False)
            if math.isnan(trough_prob) or math.isnan(peak_prob):
                log.get(get_name()).error('%s: Probability Error math.nan [%.2f%% , %.2f%%]'%(target, trough_prob, peak_prob))
                error_cnt += 1
                continue
            trough_prob_list = prob_dict.get(target, {}).get('trough', init_prob_list())
            peak_prob_list = prob_dict.get(target, {}).get('peak', init_prob_list())
            append_dict_list(prob_dict, target, trough_prob, key_sub='trough')
            append_dict_list(prob_dict, target, peak_prob, key_sub='peak')
            if trough_prob >= bollinger_limit and peak_prob >= bollinger_limit:
                log.get(get_name()).error('%s: Probability Error both > %.2f [%.2f%% , %.2f%%]'%(target, bollinger_limit, trough_prob, peak_prob))
                error_cnt += 1
                continue

            # Get continue action and increase avg_cnt as pyramid
            buy_continue, sell_continue = get_continue_cnt(trigger_action_dict.get(target, [])) # Get continue action...
            # Seems that, for example, if continue sell, then first sell in 100, second sell 110, third sell 140, something like this...

            # For example, if not continue, first take avg_cnt as default
            # if continue twice, the avg_cnt*2, step longger, make sure need to take action...
            #buy_avg_cnt = buy_continue * avg_cnt
            #sell_avg_cnt = sell_continue * avg_cnt

            # No step adjust, try using default avg_cnt for test now...
            buy_avg_cnt = sell_avg_cnt = avg_cnt
            action_type = 'sell' if all(val > bollinger_limit for val in peak_prob_list[-sell_avg_cnt:]) else \
                        'buy' if all(val > bollinger_limit for val in trough_prob_list[-buy_avg_cnt:]) else ''

            # Get price of now
            #start_time = time.time()
            try:
                now_price = get_last_price_from_db(target)
            except Exception as e:
                log.get(get_name()).error('Exception captured in get_last_price_from_db[%s]: %s'%(target, str(e)))
                time.sleep(10)
                continue
            #log.get(get_name()).debug('trigger_price_dict.get elapsed_time: %.3f'%(time.time() - start_time))    # Read database cost time
            log.get(get_name()).info('[%s]:%.2f trough[%.2f], peak[%.2f], action[%s]'%(target, now_price, trough_prob, peak_prob, action_type))
            last = trigger_price_dict.get(target, init_prob_list())[-1]     # using init_prob_list for init only, but store price data in fact

            # Get operation quantity
            quantity = 0
            price_float_th = float(get_global_config('price_float_th'))     # Reset to default every loop
            if action_type == 'sell':
                price_float_th *= sell_continue     # Ex: default_th=1.5%, Continue 3 times, then thrid time notify need have 4.5% deff
                quantity = 0
                for index in trade_order_dict.get(target, []):
                    if index['status'] == 'New':
                        quantity += index['quantity']
                clear_dict_list(trade_order_dict, target)
                if quantity == 0:
                    log.get(get_name()).debug('[%s]Nothing to Sell this time...'%(target))
                    #continue
            elif action_type == 'buy':
                price_float_th *= buy_continue
                quantity = opt_cash_limit // now_price      # This need improve....
                # get_next_inject(curr_quantity, float(get_global_config('next_inject_factor')))
                if quantity == 0:
                    log.get(get_name()).debug('[%s]No Cash to Buy this time...'%(target))
                    #continue

            # Start submit order and update data and notify to phone
            if action_type != '' and quantity > 0:
                #log.get(get_name()).debug('[%s] last[%.2f] now_price[%.2f]'%(target, last, now_price))
                price_diff = ((now_price - last) / abs(last)) if (action_type == 'sell') else ((last - now_price) / abs(last))
                if last > 0.01 and price_diff < price_float_th:
                    log.get(get_name()).info('[%s]%s, too less diff last[%.2f], Now[%.2f] RequireDiff[%.2f%%]'%(target, 
                        action_type, last, now_price, price_float_th * 100))
                    continue
                append_dict_list(trigger_price_dict, target, now_price)
                append_dict_list(trigger_action_dict, target, action_type)

                # Only submit once, avoid duplicated order...... unless you can find another way to avoid it
                #recv_dict = retry_func(get_name(), submit_order, (target, action_type, now_price, quantity,),
                #    retry_cnt=1, retry_interval=10, comment='Submit order in short_term_trade')
                recv_dict = {'test_for_now':'only notification'}
                if recv_dict != None:
                    content += '[%s]Sumbit: %s %d in %.2f,lst:%.2f\n'%(target, action_type, quantity, now_price, last)
                    log.get(get_name()).info('[%s] %s [%d] in %.2f'%(target, action_type, quantity, now_price) + ', ret: %s'%(str(recv_dict)))
                    if action_type == 'buy':
                        append_dict_list(trade_order_dict, target, {
                            'order_id': str(time.time()),
                            'price':now_price,
                            'quantity':quantity,
                            'status':'New',
                        })
                else:
                    content = 'Exception in short_term_trade [%s]submit_order: %s\n'%(target, str(e))

        if error_cnt == len(trade_list):
            log.get(get_name()).error('Error occurred in %s, exit short trade...'%(str(trade_list)))
            break
        if content != '':
            #log.get(get_name()).info(content + ', ret: %s'%(str(recv_dict)))
            retry_func(get_name(), notify.bark().send_title_content, ('Short-Orchestrator-%s'%(get_user_type('-')), content,),
                retry_cnt=3, retry_interval=60, comment='Exception in Short-Orchestrator bark')

def short_term_trade_task(queue, log_name):
    set_name(log_name)

    quantitative_init()

    house_dict = get_house_detail(get_user_type('-'))
    log.get(get_name()).info('[short_term]house_dict: %s'%(str(house_dict)))

    try:
        short_term_trade(house_dict)
    except Exception as e:
        log.get(get_name()).error('Exception in short_term_trade: %s'%(str(e)))

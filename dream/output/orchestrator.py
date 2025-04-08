#!/bin/python3

# System lib
import os
import re
import sys
import json
import time
import datetime
import argparse
import threading

import pandas as pd

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../inference'%(py_dir))
sys.path.append(r'%s/../common'%(py_dir))
from config import get_trade_list, get_global_config, get_user_config
from other import wait_us_market_open, get_user_type, get_next_inject, get_last_inject
from other import get_current_session_and_remaining_time, is_dog_option
from sock_order import submit_order, query_order, cancel_order, modify_order
from sock_realtime import query_dog_cnt, register_dog
sys.path.append(r'%s/../input'%(py_dir))
from longport_api import quantitative_init, get_cost_price_fee
from longport_api import get_open_order_from_longport, get_filled_order_from_longport
from database import get_house_detail, get_holding, create_if_order_inexist
from database import get_last_expectation, get_open_order
sys.path.append(r'%s/../inference'%(py_dir))
from expectation import get_expect
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log
log_name = '%s_%s'%(py_name, get_user_type('_'))


def query_dog_last(dog_id):
    recv_dict = query_dog_cnt(dog_id, 1)    # query last data
    if len(recv_dict['ret']) == 0:
        log.get(log_name).error('[%s]query_dog_cnt recv_dict null: %s, please check realtime service'%(dog_id, str(recv_dict)))
        return False, 0, None
    last_dict = recv_dict['ret'][0]
    last_price = float(last_dict['Price'])
    last_datetime = last_dict['DogTime'].split('-')[1]
    return True, last_price, last_datetime

def get_expect_all():
    house_name = get_user_type('-')
    house_holding = get_holding(house_name)
    tobe_trade_list = get_trade_list('us')

    notify_dict = {}
    #for hold_index in house_holding:
    for dog_index in tobe_trade_list:
        #dog_code = hold_index.get('Code')
        #dog_code_filter = dog_code[:dog_code.rfind('.US')]     # Support US market fornow
        dog_code_filter = dog_index
        if re.search(r'\d{6}', dog_code_filter):   # Search if have number like '250117'
            log.get(log_name).info('Detect share option[%s]'%(dog_code_filter))
        else:
            #log.get(log_name).info('Get expect for[%s]'%(dog_code_filter))
            next_predict = get_expect(dog_code_filter)
            if len(next_predict) != 0:
                #notify_dict.update({dog_code:next_predict})
                notify_dict.update({dog_code_filter+'.US':next_predict})   # Support US market fornow
                log.get(log_name).info('[%s]: %s'%(dog_code_filter, str(next_predict)))

    return notify_dict

def trade(house_dict, dog_opt, dog_id):
    def get_holding_by_dog_id(holding_dict, dog_id):
        for index in holding_dict:
            if index.get('Code', '') == dog_id:
                return index
        return {}
    available_cash = float(house_dict['AvailableCash'])
    log.get(log_name).info('available_cash: %.3f'%(available_cash))
    holding = get_holding_by_dog_id(json.loads(house_dict['Holding'].replace("'",'"')), dog_id)
    log.get(log_name).info('[%s] holding: %s'%(dog_id, str(holding)))
    if len(holding) == 0:
        holding.update({'Quantity':0})

    order_dest = get_user_type('-')
    create_if_order_inexist(order_dest).closeSession()  # No need db further.

    buy_price = float(dog_opt.get('buy', -1))
    sell_price = float(dog_opt.get('sell', -1))
    expct_option = dog_opt.get('option', 'NA')
    avg_score = dog_opt.get('avg_score', 0)
    curr_share = holding.get('Quantity', 0)
    bark_obj = notify.bark()
    if buy_price > 0 and available_cash > 0:
        share = get_next_inject(curr_share, float(get_global_config('next_inject_factor')))
        if (share * buy_price) > available_cash:
            log.get(log_name).info('[%s] No enough money to buy[%d], all in ......'%(dog_id, share))
            all_in_share = available_cash // buy_price
            if all_in_share * 3 < share:
                log.get(log_name).info('[%s] no need to buy, too less[%d], ignore ......'%(dog_id, all_in_share))
                share = 0
            else:
                share = all_in_share
        if share != 0:
            recv_dict = None#submit_order(dog_id, 'buy', buy_price, share)
            content = '[%s] Buy %d shares in %.2f'%(dog_id, share, buy_price)
            log.get(log_name).info(content + ', ret: %s'%(str(recv_dict)))
            bark_obj.send_title_content('Orchestrator', content)

    if sell_price > 0:
        share = get_last_inject(curr_share, float(get_global_config('next_inject_factor')))
        if share <= 0:
            log.get(log_name).info('[%s] Nothing to Sell due to share == %d......'%(dog_id, share))
        else:
            filled_order_list = get_filled_order_from_longport(dog_id, 'Buy')
            cost_price, fee = get_cost_price_fee(filled_order_list, share)
            log.get(log_name).info('[%s] Curr[%d], Cost[%.2f, %.2f] to be sell[%d]'%(dog_id, curr_share, cost_price, fee, share))
            flag, last_price, last_datetime = query_dog_last(dog_id)
            if not flag:
                log.get(log_name).error('Query last dog[%s] price failed...'%(dog_id))
            else:
                diff = ((last_price - cost_price) / cost_price) * 100
                log.get(log_name).info('[%s][%s] LastPrice[%.2f] CostPrice[%.2f] Diff[%.2f%%]'%(dog_id, last_datetime, last_price, cost_price, diff))

                if diff >= float(get_user_config(user, 'dog', 'profit_percent')):     # Sell now 
                    recv_dict = None#submit_order(dog_id, 'sell', last_price, share)
                    content = '[%s] Sell now %d shares in %.2f'%(dog_id, share, last_price)
                    log.get(log_name).info(content + ', ret: %s'%(str(recv_dict)))
                    bark_obj.send_title_content('Orchestrator', content)
                elif diff >= float(get_user_config(user, 'dog', 'min_percent')):
                    diff_lower = ((sell_price - cost_price) / cost_price) * 100
                    if diff_lower >= float(get_user_config(user, 'option', 'min_percent')):     # Set target price and wait order done
                        recv_dict = None#submit_order(dog_id, 'sell', sell_price, share)
                        content = '[%s] Sell set %d shares in %.2f'%(dog_id, share, sell_price)
                        log.get(log_name).info(content + ', ret: %s'%(str(recv_dict)))
                        bark_obj.send_title_content('Orchestrator', content)

# Skip when order already done (Filled)
# in last few min, check if the price meet the min_earn, if match, sell in current price.
# if earning achive expectation, sell in current price
def monitor_loop(order_id, dog_id, side, price, quantity):
    user, q_type= get_user_type()
    if side == 'Sell':
        filled_order_list = get_filled_order_from_longport(dog_id, 'Buy')
        cost_price, fee = get_cost_price_fee(filled_order_list, quantity)
        if cost_price < 0 or fee < 0:
            log.get(log_name).error('[%s][%s] Cannot find cost price, exit'%(order_id, dog_id))
            return False
        if is_dog_option(dog_id):
            min_diff = float(get_user_config(user, 'option', 'min_percent'))
            profit_diff = float(get_user_config(user, 'option', 'profit_percent'))
            fee = float(get_user_config(user, 'option', 'fee')) * quantity
            multiple_factor = 100   # one share means 100 dog shares
        else:
            min_diff = float(get_user_config(user, 'dog', 'min_percent'))
            profit_diff = float(get_user_config(user, 'dog', 'profit_percent'))
            fee = float(get_user_config(user, 'dog', 'fee'))
            multiple_factor = 1         # one share means one dog share
        log.get(log_name).info('Order[%s] for CostPrice[%.2f] Fee[%.2f] Quantity[%d]'%(order_id, cost_price, fee, quantity))
    elif side == 'Buy':
        pass

    bark_obj = notify.bark()
    while(True):
        time.sleep(int(get_global_config('realtime_interval')))
        recv_dict = query_order(order_id)
        log.get(log_name).debug('Query order[%s]:%s'%(order_id, str(recv_dict)))
        order_status = recv_dict['Status']
        if any(s in order_status for s in ["Filled", "Rejected", "Canceled", "Expired"]):
            content = '[%s] New Status[%s]'%(order_id, order_status)
            bark_obj.send_title_content('Order Status', content)
            return True

        flag, last_price, last_datetime = query_dog_last(dog_id)
        if not flag:
            return False
        diff = (abs(last_price - price) / price) * 100
        log.get(log_name).info('[%s][%s] LastPrice[%.2f] ExpectPrice[%.2f] Diff[%.2f%%]'%(dog_id, last_datetime, last_price, price, diff))

        now_seesion, surplus_min = get_current_session_and_remaining_time('Normal')   # Track till Normal session end
        if now_seesion == 'Post' or now_seesion == 'Night':
            log.get(log_name).info('Current Session: %s, stop monitor...'%(now_seesion))
            return  False # No need to track, wait expired
        else:
            log.get(log_name).debug('[%s][%s]Current Session: %s, continue...'%(dog_id, order_id, now_seesion))

        if side == 'Sell':
            # Formular: 
            #   earning_diff = ((last_price - cost_price) * quantity - (fee*2)) / (cost_price * quantity), to make earning_diff > expected_percent
            # But for option
            #   earning_diff = ((last_price - cost_price) * quantity * 100 - (fee*2)) / (cost_price * quantity * 100), almost option have 100 time of shares.
            # So, let multiple_factor to control.

            earning = ((last_price - cost_price) * quantity * multiple_factor) - (fee*2)
            earning_diff = earning / (cost_price * quantity * multiple_factor)

            if earning_diff >= profit_diff:
                log.get(log_name).info('Modify sell order now: [%s][%.2f][%d]'%(order_id, last_price, quantity))
                # recv_dict = modify_order(order_id, last_price, quantity)
                content = '[%s] Sell %d[%.2f] Profit-Earn[%.2f]'%(dog_id, quantity, last_price, earning)
                bark_obj.send_title_content('Profit-Earn', content)
            elif earning_diff >= min_diff:
                if surplus_min < 10:
                    log.get(log_name).info('Modify sell order due to near close: [%s][%.2f][%d]'%(order_id, last_price, quantity))
                    # recv_dict = modify_order(order_id, last_price, quantity)
                    content = '[%s] Sell %d[%.2f] Min-Earn[%.2f]'%(dog_id, quantity, last_price, earning)
                    bark_obj.send_title_content('Min-Earn', content)
                else:
                    log.get(log_name).debug('[%s][%s] earning[%.2f][%.2f%%], keep monitor'%(dog_id, order_id, earning, earning_diff))
            else:
                min_earn_price = (min_diff * (cost_price * quantity * multiple_factor) + (fee*2)) / (quantity * multiple_factor) + cost_price
                log.get(log_name).info('[%s] Min earning, now[%.2f] need achive[%.2f][%.2f%%]'%(dog_id, last_price, min_earn_price, min_diff))
        elif side == 'Buy':
            if surplus_min < 10:    # 10 min, near close market, change the price.
                if is_dog_option(dog_id):       # Enable option trade for test only, to be verify on dog trade.
                    log.get(log_name).info('Modify buy order: [%s][%.2f][%d]'%(order_id, last_price, quantity))
                    # recv_dict = modify_order(order_id, last_price, quantity)
                    content = '[%s] Buy %d[%.2f] Expect:%.2f'%(dog_id, quantity, last_price, price)
                    bark_obj.send_title_content('Test', content)

def order_monitor(order_id, dog_id, price, quantity, side):
    log.get(log_name).info('Start monitor for [%s][%s][%.2f][%s][%d]'%(order_id, dog_id, price, side, quantity))
    recv_dict = register_dog(dog_id)
    log.get(log_name).info('register realtime for: %s %s'%(dog_id, str(recv_dict)))
    monitor_loop(order_id, dog_id, side, price, quantity)

# According exist order to trade.
# Reason: usually in us dog trade, our body need to sleep, cannot watch the dog market.
# Then, we could submit an order to make this function to track
# Once reach the expected earning, modify the price and share.
# Support Sell only for now...
def trigger_order_monitor():
    user, quent_type = get_user_type()
    bark_obj = notify.bark()
    thread_dict = {}
    while(True):
        db_opened_order_list = get_open_order(user, quent_type)
        #log.get(log_name).info('db_opened_order_list %s'%(str(db_opened_order_list)))
        api_opened_order_list = get_open_order_from_longport()
        #log.get(log_name).info('api_opened_order_list %s'%(str(api_opened_order_list)))
        opened_order_list = list({item['OrderID']: item for item in db_opened_order_list + api_opened_order_list}.values())
        log.get(log_name).debug('opened_order_list %s'%(str(opened_order_list)))
        if len(api_opened_order_list) != 0:     # Try from longport
            order_dest = get_user_type('-')
            db = create_if_order_inexist(order_dest)
            for order_index in api_opened_order_list:
                if order_index['OrderID'] in {order['OrderID'] for order in db_opened_order_list}:
                    continue
                log.get(log_name).info('Got open order from longport, start insert: %s'%(str(order_index)))
                if not db.insert_order(order_dest, order_index):
                    log.get(log_name).error('Order Inser Error...[%s] %s'%(order_dest, str(order_index)))
            db.closeSession()

        content = ''
        for order_index in opened_order_list:
            order_id = order_index['OrderID']
            order_status = order_index['Status']
            dog_id = order_index['Code'].replace('.US','')
            if order_status.find('Filled') >= 0:
                log.get(log_name).info('[%s][%s] Already in Filled status [%s]'%(order_id, dog_id, order_status))
                continue    # Filled & PartialFilledStatus , already in loop, skip...
            if order_id in thread_dict:
                log.get(log_name).debug('[%s][%s] Already created thread'%(order_id, dog_id))
                continue

            price = float(order_index['Price'])
            quantity = int(order_index['Quantity'].split('/')[1])
            side = order_index['Side']

            content += '[%s] %s %d in Price[%.2f]\n'%(dog_id, side, quantity, price)
            monitor_t = threading.Thread(target=order_monitor, args=(order_id, dog_id, price, quantity, side, ))
            monitor_t.start()
            thread_dict.update({order_id:monitor_t})
        if len(content) > 0:
            bark_obj.send_title_content('Monitor Trigger', content)

        time.sleep(int(get_global_config('order_monitor_interval')))
        now_seesion, surplus_min = get_current_session_and_remaining_time('Normal')   # Track till Normal session end
        if now_seesion == 'Post' or now_seesion == 'Night':
            log.get(log_name).info('Current Session: %s, stop order detection...'%(now_seesion))
            break

    return thread_dict


def main(args):
    log.init('%s/../log'%(py_dir), log_name, log_mode='w', log_level='debug', console_enable=True)
    log.get(log_name).info('Logger Creat Success...[%s]'%(log_name))

    if not args.test:
        wait_us_market_open(log.get(log_name))

    expectation_dict = get_last_expectation('us', today=False)
    log.get(log_name).info('expectation_dict: %s'%(str(expectation_dict)))

    quantitative_init()
    house_dict = get_house_detail(get_user_type('-'))
    log.get(log_name).info('house_dict: %s'%(str(house_dict)))

    # Submit order
    for index in expectation_dict:
        dog_opt = expectation_dict[index]
        dog_id = index
        if dog_id.rfind('.US') <= 0:
            dog_id = index + '.US'
        trade(house_dict, dog_opt, dog_id)

    thread_dict = trigger_order_monitor()
    for order_id in thread_dict:
        thread_dict[order_id].join()

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)


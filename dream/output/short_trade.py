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
sys.path.append(r'%s/../common'%(py_dir))
from config import get_trade_list, get_global_config, get_user_config
from other import wait_us_market_open, get_user_type, get_current_session_and_remaining_time, is_dog_option
from sock_order import submit_order, query_order, cancel_order, modify_order
from sock_realtime import query_dog, register_dog
from database import get_open_order, del_registered_dog, create_if_order_inexist
from longport_api import quantitative_init, get_order_detail
from longport_api import get_open_order_from_longport, get_filled_order_from_longport
sys.path.append(r'%s/../input'%(py_dir))
sys.path.append(r'%s/../inference'%(py_dir))
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log



# According exist order to trade.
# Reason: usually in us dog trade, we need to sleep, cannot watch the dog market.
# Then, we could submit a over price order to make this function to track at first, 
# Once reach the expected earning, modify the price and share.
# Support Sell only.
def trade_half_manually():
    user, quent_type = get_user_type()
    opened_order_list = get_open_order(user, quent_type)
    log.get().info('opened_order_list %s'%(str(opened_order_list)))
    if len(opened_order_list) == 0:     # Try from longport
        opened_order_list = get_open_order_from_longport()
        order_dest = get_user_type('-')
        db = create_if_order_inexist(order_dest)
        for order_index in opened_order_list:
            log.get().info('Got open order from longport, start insert: %s'%(str(order_index)))
            if not db.insert_order(order_dest, order_index):
                log.get().error('Order Inser Error...[%s] %s'%(order_dest, str(order_index)))
        db.closeSession()

    bark_obj = notify.bark()
    content = ''
    thread_dict = {}
    for order_index in opened_order_list:
        order_id = order_index['OrderID']
        order_status = order_index['Status']
        if order_status.find('Filled') >= 0 or order_id in thread_dict:
            continue    # Filled & PartialFilledStatus , already in loop, skip...
        dog_id = order_index['Code'].replace('.US','')
        price = float(order_index['Price'])
        quantity = int(order_index['Quantity'].split('/')[1])
        side = order_index['Side']

        content += '[%s] %s %d in Price[%.2f]'%(dog_id, side, price, quantity)
        monitor_t = threading.Thread(target=half_manually_monitor, args=(order_id, dog_id, price, quantity, side, ))
        monitor_t.start()
        thread_dict.update({order_id:monitor_t})
    bark_obj.send_title_content('Short Trade Monitor', content)

    for order_id in thread_dict:
        thread_dict[order_id].join()

def get_cost_price_fee(filled_order_list, quantity):
    match_list = []
    for index in filled_order_list:
        temp_quantity = int(index['Quantity'].split('/')[0])    # Get position 0 for actrully success share. (x/y)
        if quantity == temp_quantity:
            match_list.append(index)

    last_datetime = datetime.datetime.strptime('2000-01-01 01:01:01', '%Y-%m-%d %H:%M:%S')
    last_order = None
    for index in match_list:
        order_datetime = datetime.datetime.strptime(index['Date'], '%Y-%m-%d %H:%M:%S.%f')
        if order_datetime > last_datetime:
            last_datetime = order_datetime
            last_order = index

    if last_order != None:
        #resp = get_order_detail(last_order['OrderID'])     # Get fee detail fail from this api, don't know why...
        log.get(py_name).info('Last Order Detail: %s'%(str(last_order)))
        return float(last_order['Price']), float(last_order['Fee'])

    return -0.1, -0.1

def buy_loop(order_id, dog_id, price, quantity):
    return

# Skip when order already done (Filled)
# in last few min, check if the price meet the min_earn, if match, sell in current price.
# if earning achive expectation, sell in current price
def selling_loop(order_id, dog_id, price, quantity):
    user, q_type= get_user_type()
    filled_order_list = get_filled_order_from_longport(dog_id, 'Buy')
    cost_price, fee = get_cost_price_fee(filled_order_list, quantity)
    if is_dog_option(dog_id):
        min_earn = float(get_user_config(user, 'option', 'min_earn'))
        expect_earn = float(get_user_config(user, 'option', 'expect_earn'))
        fee = float(get_user_config(user, 'option', 'fee'))
    else:
        min_earn = float(get_user_config(user, 'dog', 'min_earn'))
        expect_earn = float(get_user_config(user, 'dog', 'expect_earn'))
        fee = float(get_user_config(user, 'dog', 'fee'))
    log.get(py_name).info('This order for CostPrice[%.2f] Fee[%.2f] Quantity[%d]'%(cost_price, fee, quantity))

    while(True):
        time.sleep(int(get_global_config('realtime_interval')))
        recv_dict = query_order(order_id)
        order_status = recv_dict['Status']
        if order_status.find('Filled') >= 0:
            return

        recv_dict = query_dog(dog_id, (int(get_global_config('realtime_interval')) // 60) * 2)    # query last data, double time for ensurement
        if len(recv_dict['ret']) == 0:
            recv_dict = query_dog(dog_id, 24 * 60)     # Try get in last 24 hours
        if len(recv_dict['ret']) == 0:
            log.get(py_name).error('query_dog recv_dict null even in last 24 hour: %s'%(str(recv_dict)))
            return
        last_dict = recv_dict['ret'][-1]
        last_price = float(last_dict['Price'])
        last_datetime = last_dict['DogTime'].split('-')[1]
        log.get(py_name).info('[%s] Last Price[%.2f] Time[%s]'%(dog_id, last_price, last_datetime))

        # Formular: earning = (last_price - cost_price) * quantity - (fee*2), to make earning > value
        # Then, last_price = (value + (fee*2)) / quantity + cost_price
        min_earn_price = (min_earn + (fee*2)) / quantity + cost_price

        if (last_price < cost_price):   # Still under cost_price
            min_earn_diff = (abs(min_earn_price - last_price) / last_price)
            log.get(py_name).info('[%s] If need achive min earning, need diff[%.2f][%.2f%%] from now[%.2f]'%(dog_id, min_earn_price, min_earn_diff*100, last_price))
            continue
        else:
            now_seesion, surplus_min = get_current_session_and_remaining_time('Normal')   # Track till Normal session end
            if now_seesion == 'Post' or now_seesion == 'Night':
                log.get(py_name).info('Current Session: %s, stop monitor...'%(now_seesion))
                return  # No need to track, wait expired
            earning = (last_price - cost_price) * quantity - (fee*2)
            if (surplus_min < 10 and earning > min_earn) or earning > expect_earn:    # 10 min, near close market or reach expected, change the price.
                recv_dict = modify_order(order_id, last_price, quantity)
                log.get(py_name).info('modify_order recv_dict: %s'%(str(recv_dict)))
                bark_obj = notify.bark()
                content = '[%s] Sell reach change to price[%.2f], Earn[%.2f]'%(dog_id, last_price, earning)
                bark_obj.send_title_content('Short Trade Success', content)
                return

def half_manually_monitor(order_id, dog_id, price, quantity, side):
    log.get(py_name).info('Start monitor for [%s][%s][%.2f][%d]'%(order_id, dog_id, price, quantity))
    recv_dict = register_dog(dog_id)
    log.get(py_name).info('register realtime for: %s %s'%(dog_id, str(recv_dict)))

    if side == 'Sell':
        selling_loop(order_id, dog_id, price, quantity)
    elif side == 'Buy':
        buy_loop(order_id, dog_id, price, quantity)

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success...[%s]'%(py_name))

    quantitative_init()

    if not args.test:
        wait_us_market_open(log.get())

    trade_half_manually()

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)
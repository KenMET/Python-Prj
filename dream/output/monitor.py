#!/usr/bin/ python3

import os
import sys
import time
import logging
import datetime
import threading

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../input'%(py_dir))
from house import house_update
from longport_api import get_order_detail, cancel_order, get_last_price, is_order_invalid
from database import get_house_detail, get_holding, get_market_by_range, create_if_order_inexist
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

monitor_dict = {}
def update(order_dest, order_dict):
    global monitor_dict
    temp_list = monitor_dict.get(order_dest, [])
    temp_list.append(order_dict)
    monitor_dict.update({order_dest:temp_list})

def get_by_id(order_dest, order_id):
    global monitor_dict
    temp_list = monitor_dict.get(order_dest, [])
    for index in temp_list:
        if index['OrderID'] == order_id:
            return index
    return None

def adject_interval(curr_price, submit_price):
    diff = abs(curr_price - submit_price) / submit_price
    if diff > 0.2:      # over 20%
        return 60 * 60 * 2  # 2 hour
    elif diff > 0.1:    # over 10%
        return 60 * 60 * 1  # 1 hour
    elif diff > 0.05:   # over 5%
        return 60 * 30      # 30 minutes
    elif diff > 0.02:   # over 2%
        return 60 * 10      # 10 minutes
    elif diff > 0.01:   # over 1%
        return 60 * 5       # 5 minutes
    elif diff > 0.005:  # over 0.5%
        return 60 * 2       # 2 minutes
    else:               # less then 0.5%
        return 60 * 1       # 1 minutes

def get_next_close_time(submit_time):
    next_day = submit_time + datetime.timedelta(days=1)
    next_day_time = next_day.replace(hour=7, minute=50, second=0, microsecond=0)
    return next_day_time

def is_openning(submit_time):
    current_time = datetime.datetime.now()
    if current_time > get_next_close_time(submit_time):
        return False    # Not open
    return True

def is_near_close(submit_time, interval):
    current_time = datetime.datetime.now()
    next_time = current_time + datetime.timedelta(seconds=interval)
    if next_time > get_next_close_time(submit_time):
        return True     # curr + interval  >  close, so need to stop timer
    return False

def start_monitor(calling_name, order_dest, order_dict):
    cnt = 0
    order_id = order_dict['OrderID']
    if get_by_id(order_dest, order_id) == None:
        order_dict.update({'cnt':0})
        update(order_dest, order_dict)
        log.get(calling_name).info('First insert [%s]'%(order_id))
    else:
        cnt = order_dict['cnt'] + 1
        order_dict.update({'cnt':cnt})
        temp_dict = get_order_detail(order_id)
        order_dict.update(temp_dict)
        log.get(calling_name).info('Looping to get order detail [%s]'%(str(temp_dict)))
        db = create_if_order_inexist(order_dest)
        db.update_order_by_id(order_dest, order_id, temp_dict)      # update to database
        update(order_dest, order_dict)                              # update to local dict
    
    submit_date = order_dict['Date']
    curr_price = get_last_price(order_dict['Code'])
    submit_price = float(order_dict['Price'])
    interval = adject_interval(curr_price, submit_price)
    if is_openning(submit_date) and not is_near_close(submit_date, interval) and not is_order_invalid(order_dict):
        log.get(calling_name).info('Monitor for [%s] start round[%d] as interval[%d]'%(order_id, cnt, interval))
        timer = threading.Timer(interval, start_monitor, args=(calling_name, order_dest, order_dict))
        timer.start()
    else:
        log.get(calling_name).info('Monitor Cancel for [%s] monitored[%d]'%(order_id, cnt))
        if not is_order_invalid(order_dict):
            log.get(calling_name).info('Order[%s] still valid, Cancel'%(order_id))
            cancel_order(order_id)

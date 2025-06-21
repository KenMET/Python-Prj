#!/bin/python3

# System lib
import os
import sys
import time
import threading

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../common'%(py_dir))
from config import get_global_config, get_user_config
from other import get_user_type, append_dict_list, clear_dict_list, retry_func
from other import get_current_session_and_remaining_time, is_dog_option
from sock_order import submit_order, query_order, cancel_order, modify_order
from sock_realtime import register_dog
sys.path.append(r'%s/../input'%(py_dir))
from longport_api import quantitative_init, get_cost_price_fee
from longport_api import get_open_order_from_longport, get_filled_order_from_longport
from database import create_if_order_inexist, get_open_order, get_dog_realtime_cnt
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


def query_dog_last(dog_id):
    temp_list = get_dog_realtime_cnt(dog_id, 1)    # query last data
    if len(temp_list) != 1:
        log.get(get_name()).error('[%s]get_dog_realtime_cnt temp_list null: %s, please check realtime service'%(dog_id, str(temp_list)))
        return False, 0, None
    last_dict = temp_list[-1]
    last_price = float(last_dict['Price'])
    last_datetime = last_dict['DogTime'].split('-')[1]
    return True, last_price, last_datetime

# Skip when order already done (Filled)
# in last few min, check if the price meet the min_earn, if match, sell in current price.
# if earning achive expectation, sell in current price
def monitor_loop(order_id, dog_id, side, price, quantity):
    user, q_type= get_user_type()
    if side == 'Sell':
        filled_order_list = get_filled_order_from_longport(dog_id, 'Buy')
        cost_price, fee = get_cost_price_fee(filled_order_list, quantity)
        if cost_price < 0 or fee < 0:
            log.get(get_name()).error('[%s][%s] Cannot find cost price, exit'%(order_id, dog_id))
            return False
        if is_dog_option(dog_id):
            min_diff = float(get_user_config(user, 'option', 'min_percent'))
            profit_diff = float(get_user_config(user, 'option', 'profit_percent'))
            fee = float(get_user_config(user, 'option', 'fee')) * quantity
            multiple_factor = 100   # one quantity means 100 dog quantity
        else:
            min_diff = float(get_user_config(user, 'dog', 'min_percent'))
            profit_diff = float(get_user_config(user, 'dog', 'profit_percent'))
            fee = float(get_user_config(user, 'dog', 'fee'))
            multiple_factor = 1         # one quantity means one dog quantity
        log.get(get_name()).info('[%s]Order[%s] for CostPrice[%.2f] Fee[%.2f] Quantity[%d] multiple_factor[%d]'%(dog_id, 
            order_id, cost_price, fee, quantity, multiple_factor))
    elif side == 'Buy':
        pass

    while(True):
        time.sleep(int(get_global_config('realtime_interval')))
        recv_dict = retry_func(get_name(), query_order, (order_id,),
            retry_cnt=3, retry_interval=10, comment='Query order in order monitor')
        if recv_dict == None:
            log.get(get_name()).error('Query order[%s] failed, sleep and skip this round'%(order_id))
            time.sleep(int(get_global_config('realtime_interval')))
            continue

        log.get(get_name()).debug('Query order[%s]:%s'%(order_id, str(recv_dict)))
        order_status = recv_dict.get('Status', '')
        if order_status == '':
            continue
        price = recv_dict['Price']      # Need update price in case of modified order
        if any(s in order_status for s in ["Filled", "Rejected", "Canceled", "Expired"]):
            content = '[%s] New Status[%s]'%(order_id, order_status)
            retry_func(get_name(), notify.bark().send_title_content, ('Order-Status', content,),
                retry_cnt=3, retry_interval=60, comment='Exception in Order-Status bark')
            return True

        flag, last_price, last_datetime = query_dog_last(dog_id)
        if not flag:
            return False
        diff = (abs(last_price - price) / abs(price)) * 100
        log.get(get_name()).info('[%s][%s] LastPrice[%.2f] ExpectPrice[%.2f] Diff[%.2f%%]'%(dog_id, last_datetime, last_price, price, diff))

        now_seesion, surplus_min = get_current_session_and_remaining_time('Normal')   # Track till Normal session end
        if now_seesion == 'Post' or now_seesion == 'Night':
            log.get(get_name()).info('Current Session: %s, stop monitor...'%(now_seesion))
            return  False # No need to track, wait expired
        else:
            log.get(get_name()).debug('[%s][%s]Current Session: %s, continue...'%(dog_id, order_id, now_seesion))

        modify_dict = {}
        if side == 'Sell':
            # Formular: 
            #   earning_diff = ((last_price - cost_price) * quantity - (fee*2)) / (cost_price * quantity), to make earning_diff > expected_percent
            # But for option
            #   earning_diff = ((last_price - cost_price) * quantity * 100 - (fee*2)) / (cost_price * quantity * 100), almost option have 100 time of shares.
            # So, let multiple_factor to control.

            earning = ((last_price - cost_price) * quantity * multiple_factor) - (fee*2)
            earning_diff = (earning / (cost_price * quantity * multiple_factor)) * 100
            if earning_diff >= profit_diff:
                log.get(get_name()).info('[%s]Modify sell order now: [%s][%.2f][%d]'%(dog_id, order_id, last_price, quantity))
                content = '[%s] Sell %d[%.2f] Profit-Earn[%.2f]'%(dog_id, quantity, last_price, earning)
                modify_dict.update({'opt_direction':'sell', 'opt_order_id':order_id, 'opt_price':last_price, 'opt_quantity':quantity})
            elif earning_diff >= min_diff:
                if surplus_min < 10:
                    log.get(get_name()).info('[%s]Modify sell order due to near close: [%s][%.2f][%d]'%(dog_id, order_id, last_price, quantity))
                    modify_dict.update({'opt_direction':'sell', 'opt_order_id':order_id, 'opt_price':last_price, 'opt_quantity':quantity})
                    content = '[%s] Sell %d[%.2f] Min-Earn[%.2f]'%(dog_id, quantity, last_price, earning)
                else:
                    log.get(get_name()).debug('[%s][%s] earning[%.2f][%.2f%%], keep monitor'%(dog_id, order_id, earning, earning_diff))
            else:
                min_earn_price = ((min_diff/100) * (cost_price * quantity * multiple_factor) + (fee*2)) / (quantity * multiple_factor) + cost_price
                log.get(get_name()).info('[%s] Min earning, now[%.2f] need achive[%.2f][%.2f%%]'%(dog_id, last_price, min_earn_price, min_diff))
        elif side == 'Buy':
            if surplus_min < 10:    # 10 min, near close market, change the price.
                if is_dog_option(dog_id):       # Enable option trade for test only, to be verify on dog trade.
                    log.get(get_name()).info('Modify buy order: [%s][%.2f][%d]'%(order_id, last_price, quantity))
                    modify_dict.update({'opt_direction':'buy', 'opt_order_id':order_id, 'opt_price':last_price, 'opt_quantity':quantity})
                    content = '[%s] Buy %d[%.2f] Expect:%.2f'%(dog_id, quantity, last_price, price)

        if len(modify_dict) != 0:
            opt_direction = modify_dict.get('opt_direction')
            opt_order_id = modify_dict.get('opt_order_id')
            opt_price = modify_dict.get('opt_price')
            opt_quantity = modify_dict.get('opt_quantity')
            recv_dict = {'test_for_now':'only notification'}
            #recv_dict = retry_func(get_name(), modify_order, (opt_order_id, opt_price, opt_quantity,),
            #    retry_cnt=2, retry_interval=10, comment='Modify order in order monitor')
            if recv_dict != None:
                content = '[%s][%s] %s modify to %.2f\n'%(dog_id, opt_order_id, opt_direction, opt_price)
                log.get(get_name()).info(content.replace('\n','') + ', ret: %s'%(str(recv_dict)))
            else:
                content = 'Exception captured in trade modify_order: %s\n'%(str(e))
            retry_func(get_name(), notify.bark().send_title_content, ('Order-Monitor', content,),
                retry_cnt=3, retry_interval=60, comment='Exception in Order-Monitor bark')

def order_monitor(order_id, dog_id, price, quantity, side):
    log.get(get_name()).info('Start monitor for [%s][%s][%.2f][%s][%d]'%(order_id, dog_id, price, side, quantity))
    try:
        recv_dict = register_dog(dog_id)
        log.get(get_name()).info('[order_monitor]register realtime for: %s %s'%(dog_id, str(recv_dict)))
    except Exception as e:
        log.get(get_name()).error('Exception captured in order_monitor register_dog: %s'%(str(e)))
    monitor_loop(order_id, dog_id, side, price, quantity)

# According exist order to trade.
# Reason: usually in us dog trade, our body need to sleep, cannot watch the dog market.
# Then, we could submit an order to make this function to track
# Once reach the expected earning, modify the price and quantity.
# Support Sell only for now...
def trigger_order_monitor():
    thread_dict = {}
    log.get(get_name()).info('[Order Monitor]Starting loop...')
    while(True):
        db_opened_order_list = get_open_order()
        #log.get(get_name()).info('db_opened_order_list %s'%(str(db_opened_order_list)))
        api_opened_order_list = retry_func(get_name(), get_open_order_from_longport, (),
            retry_cnt=3, retry_interval=int(get_global_config('order_monitor_interval')), 
            comment='Exception in get_open_order_from_longport')
        opened_order_list = list({item['OrderID']: item for item in db_opened_order_list + api_opened_order_list}.values())
        log.get(get_name()).debug('opened_order_list %s'%(str(opened_order_list)))
        if len(api_opened_order_list) != 0:     # Try from longport
            order_dest = get_user_type('-')
            db = create_if_order_inexist(order_dest)
            for order_index in api_opened_order_list:
                if order_index['OrderID'] in {order['OrderID'] for order in db_opened_order_list}:
                    continue
                log.get(get_name()).info('Got open order from longport, start insert: %s'%(str(order_index)))
                if not db.insert_order(order_dest, order_index):
                    log.get(get_name()).error('Order Inser Error...[%s] %s'%(order_dest, str(order_index)))
            db.closeSession()

        content = ''
        for order_index in opened_order_list:
            order_id = order_index['OrderID']
            order_status = order_index['Status']
            dog_id = order_index['Code'].replace('.US','')
            if order_status.find('Filled') >= 0:
                log.get(get_name()).info('[%s][%s] Already in Filled status [%s]'%(order_id, dog_id, order_status))
                continue    # Filled & PartialFilledStatus , already in loop, skip...
            if order_id in thread_dict:
                log.get(get_name()).debug('[%s][%s] Already created thread'%(order_id, dog_id))
                continue

            price = float(order_index['Price'])
            quantity = int(order_index['Quantity'].split('/')[1])
            side = order_index['Side']

            content += '[%s]Order Detected: %s %d in Price[%.2f]\n'%(dog_id, side, quantity, price)
            monitor_t = threading.Thread(target=order_monitor, args=(order_id, dog_id, price, quantity, side, ))
            monitor_t.start()
            thread_dict.update({order_id:monitor_t})
        if len(content) > 0:
            retry_func(get_name(), notify.bark().send_title_content, ('Monitor-Trigger', content,),
                retry_cnt=3, retry_interval=60, comment='Exception in Monitor-Trigger bark')

        time.sleep(int(get_global_config('order_monitor_interval')))
        now_seesion, surplus_min = get_current_session_and_remaining_time('Post')   # Track till Post session end
        if now_seesion == 'Night':
            log.get(get_name()).info('Current Session: %s, stop order detection...'%(now_seesion))
            break

    return thread_dict

def order_monitor_task(queue, log_name):
    set_name(log_name)

    quantitative_init()

    # Start order monitor
    thread_dict = {}
    try:
        thread_dict = trigger_order_monitor()
    except Exception as e:
        log.get(get_name()).error('Exception in trigger_order_monitor: %s'%(str(e)))

    for order_id in thread_dict:
        thread_dict[order_id].join()
    short_trade_t.join()



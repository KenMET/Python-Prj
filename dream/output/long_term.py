#!/bin/python3

# System lib
import os
import sys
import json
import math
import time

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../common'%(py_dir))
from config import get_global_config, get_user_config
from other import get_user_type, get_next_inject, get_prev_inject
from sock_order import submit_order, query_order, cancel_order, modify_order
from sock_realtime import register_dog
sys.path.append(r'%s/../input'%(py_dir))
from longport_api import quantitative_init, get_cost_price_fee
from longport_api import get_filled_order_from_longport
from database import create_if_order_inexist, get_house_detail, get_holding
from database import get_last_expectation, get_last_price_from_db, get_dog_realtime_cnt
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

def long_term_trade(house_dict, dog_opt, dog_id):
    def get_holding_by_dog_id(holding_dict, dog_id):
        for index in holding_dict:
            if index.get('Code', '').find(dog_id+'.') >= 0:
                return index
        return {}
    try:
        recv_dict = register_dog(dog_id)
        log.get(get_name()).info('[long_term_trade]register realtime for: %s %s'%(dog_id, str(recv_dict)))
    except Exception as e:
        log.get(get_name()).error('Exception captured in long_term_trade register_dog: %s'%(str(e)))
    try:
        
        available_cash = float(house_dict['AvailableCash'])
        log.get(get_name()).info('available_cash: %.3f'%(available_cash))
        holding = get_holding_by_dog_id(json.loads(house_dict['Holding'].replace("'",'"')), dog_id)
        log.get(get_name()).info('[%s] holding: %s'%(dog_id, str(holding)))
        if len(holding) == 0:
            holding.update({'Quantity':0})

        user, q_type= get_user_type()
        order_dest = user + '-' + q_type
        create_if_order_inexist(order_dest).closeSession()  # No need db further.

        trough_prob = float(dog_opt.get('trough', -1.0))
        peak_prob = float(dog_opt.get('peak', -1.0))
        last_price = float(dog_opt.get('last_price', -1.0))
        if last_price < 0.0 or trough_prob < 0.0 or peak_prob < 0.0:
            content = 'Format error in dog_opt: %s\n'%(str(dog_opt))
            log.get(get_name()).error(content.replace('\n', ''))
            return content

        last_price = get_last_price_from_db(dog_id)     # update last price
        steepness = float(get_global_config('price_steepness'))
        bollinger_limit = float(get_global_config('bollinger_limit'))
        buy_price = last_price if (trough_prob > 99.0) else (last_price + math.log(trough_prob/100)/steepness)
        buy_price = (-1.0) if (trough_prob < bollinger_limit) else buy_price
        sell_price = last_price if (peak_prob > 99.0) else (last_price - math.log(peak_prob/100)/steepness)
        sell_price = (-1.0) if (peak_prob < bollinger_limit) else sell_price
        #log.get(get_name()).info('[%s]trough_: %.2f%% peak:%.2f%% last_price:%.2f [%.2f, %.2f]'%(
        #    dog_id, trough_prob, peak_prob, last_price, buy_price, sell_price))
        avg_score = dog_opt.get('avg_score', 0)
        curr_quantity = holding.get('Quantity', 0)
        content = 'Monitoring today'
        submit_dict = {}
        if buy_price > 0 and available_cash > 0:
            quantity = get_next_inject(curr_quantity, float(get_global_config('next_inject_factor')))
            if (quantity * buy_price) > available_cash:
                log.get(get_name()).info('[%s] No enough money to buy[%d], all in ......'%(dog_id, quantity))
                all_in_quantity = available_cash // buy_price
                if all_in_quantity * 3 < quantity:
                    log.get(get_name()).info('[%s] no need to buy, too less[%d], ignore ......'%(dog_id, all_in_quantity))
                    quantity = 0
                else:
                    quantity = all_in_quantity
            if quantity != 0:
                submit_dict.update({'opt_direction':'buy', 'opt_price':buy_price, 'opt_quantity':quantity})
        elif sell_price > 0:
            quantity = get_prev_inject(curr_quantity, float(get_global_config('next_inject_factor')))
            if quantity <= 0:
                content = '[%s] Nothing to Sell[%d]\n'%(dog_id, quantity)
                log.get(get_name()).info(content.replace('\n',''))
            else:
                filled_order_list = get_filled_order_from_longport(dog_id, 'Buy')
                cost_price, fee = get_cost_price_fee(filled_order_list, quantity)
                log.get(get_name()).info('[%s] Curr[%d], Cost[%.2f, %.2f] to be sell[%d]'%(dog_id, curr_quantity, cost_price, fee, quantity))
                flag, last_price, last_datetime = query_dog_last(dog_id)
                if not flag:
                    log.get(get_name()).error('Query last dog[%s] price failed...'%(dog_id))
                else:
                    diff = ((last_price - cost_price) / abs(cost_price)) * 100
                    log.get(get_name()).info('[%s][%s] LastPrice[%.2f] CostPrice[%.2f] Diff[%.2f%%]'%(dog_id, last_datetime, last_price, cost_price, diff))
                    if diff >= float(get_user_config(user, 'dog', 'profit_percent')):     # Sell now 
                        submit_dict.update({'opt_direction':'sell', 'opt_price':last_price, 'opt_quantity':quantity})
                    elif diff >= float(get_user_config(user, 'dog', 'min_percent')):
                        diff_lower = ((sell_price - cost_price) / cost_price) * 100
                        if diff_lower >= float(get_user_config(user, 'option', 'min_percent')):     # Set target price and wait order done
                            submit_dict.update({'opt_direction':'sell', 'opt_price':sell_price, 'opt_quantity':quantity})

        retry_time = 2
        while (retry_time > 0):
            try:
                if len(submit_dict) != 0:
                    opt_direction = submit_dict.get('opt_direction')
                    opt_price = submit_dict.get('opt_price')
                    opt_quantity = submit_dict.get('opt_quantity')
                    recv_dict = submit_order(dog_id, opt_direction, opt_price, opt_quantity)
                    content = '[%s] %s set %d quantity in %.2f, last:%.2f\n'%(dog_id, opt_direction, opt_quantity, opt_price, last_price)
                    log.get(get_name()).info(content.replace('\n','') + ', ret: %s'%(str(recv_dict)))
                break
            except Exception as e:
                retry_time -= 1
                log.get(get_name()).error('Exception captured in long_term_trade submit_order: %s, retry:%d'%(str(e), retry_time))
                time.sleep(10)
        if retry_time == 0:
            content = 'Exception captured in long_term_trade submit_order: %s\n'%(str(e))
        return content
    except Exception as e:
        content = 'Exception captured in long_term_trade: %s\n'%(str(e))
        log.get(get_name()).error(content.replace('\n',''))
        return content


def long_term_trade_task(queue, log_name):
    set_name(log_name)

    quantitative_init()
    expectation_dict = get_last_expectation('us', today=True)
    log.get(get_name()).info('[long_term]expectation_dict: %s'%(str(expectation_dict)))

    house_dict = get_house_detail(get_user_type('-'))
    log.get(get_name()).info('[long_term]house_dict: %s'%(str(house_dict)))

    # Submit order for Long-term trade
    content = ''
    for dog_index in expectation_dict:
        dog_opt = expectation_dict[dog_index]
        content += long_term_trade(house_dict, dog_opt, dog_index)
    try:
        if content != '':
            notify.bark().send_title_content('Long-Orchestrator-%s'%(get_user_type('-')), content)
    except Exception as e:
        log.get(get_name()).error('Exception captured in Long-Orchestrator bark[%s]: %s'%(content, str(e)))



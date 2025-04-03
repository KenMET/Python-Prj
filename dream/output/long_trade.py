#!/bin/python3

# System lib
import os
import re
import sys
import json
import datetime
import argparse
import subprocess

import pandas as pd

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../inference'%(py_dir))
from strategy import get_stategy_handle
sys.path.append(r'%s/../common'%(py_dir))
from config import get_trade_list
from other import wait_us_market_open, get_user_type
from sock_order import submit_order
sys.path.append(r'%s/../input'%(py_dir))
from house import house_update
from longport_api import quantitative_init, trade_submit
from database import get_house_detail, get_holding, get_market_by_range, create_if_order_inexist
from database import get_last_expectation
sys.path.append(r'%s/../inference'%(py_dir))
from expectation import get_expect
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log
log_name = '%s_%s'%(py_name, get_user_type('_'))


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

    for side in dog_opt:
        price = float(dog_opt[side])
        curr_share = holding.get('Quantity')
        share = 0
        if side == 'buy':
            if curr_share == 0:
                share = 1
            else:
                share = curr_share * 2  # buy double
            if (share * price) > available_cash:
                log.get(log_name).info('[%s] No enough money to buy[%d], all in ......'%(dog_id, share))
                all_in_share = available_cash // price
                if all_in_share * 3 < share:
                    log.get(log_name).info('[%s] no need to buy, too less[%d], ignore ......'%(dog_id, all_in_share))
                    share = 0
                else:
                    share = all_in_share
        elif side == 'sell':
            if (curr_share == 0):
                continue
            share = curr_share // 2
        else:
            continue
        if share == 0:
            log.get(log_name).info('[%s] Nothing to opt due to share == 0......'%(dog_id))
            continue

        submit_order(dog_id, side, price, share)

        log.get(log_name).info('[%s] %s %d shares in price %.2f'%(dog_id, side, share, price))
    

def main(args):
    log.init('%s/../log'%(py_dir), log_name, log_mode='w', log_level='info', console_enable=True)
    log.get(log_name).info('Logger Creat Success...[%s]'%(log_name))

    if not args.test:
        wait_us_market_open(log.get(log_name))

    expectation_dict = get_last_expectation('us', today=True)
    log.get(log_name).info('expectation_dict: %s'%(str(expectation_dict)))

    #result = subprocess.run(["python3", "%s/../input/house.py"], capture_output=True, text=True)
    predict_dict = get_expect_all()
    log.get(log_name).info('Predict result: %s'%(str(predict_dict)))

    quantitative_init()
    house_dict = get_house_detail(get_user_type('-'))

    # Submit order
    for index in predict_dict:
        dog_opt = predict_dict[index]
        trade(house_dict, dog_opt, index)

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)
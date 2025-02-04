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
from standard import wait_us_market_open
from order import submit_order
sys.path.append(r'%s/../input'%(py_dir))
from house import house_update
from longport_api import quantitative_init, trade_submit
from database import get_house_detail, get_holding, get_market_by_range, create_if_order_inexist
sys.path.append(r'%s/../inference'%(py_dir))
from expectation import get_expect
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log


def get_expect_all(quent_type, user_name):
    house_name = '%s-%s'%(quent_type, user_name)
    house_holding = get_holding(house_name)
    tobe_trade_list = get_trade_list('us')

    notify_dict = {}
    #for hold_index in house_holding:
    for dog_index in tobe_trade_list:
        #dog_code = hold_index.get('Code')
        #dog_code_filter = dog_code[:dog_code.rfind('.US')]     # Support US market fornow
        dog_code_filter = dog_index
        if re.search(r'\d{6}', dog_code_filter):   # Search if have number like '250117'
            log.get().info('Detect share option[%s]'%(dog_code_filter))
        else:
            #log.get().info('Get expect for[%s]'%(dog_code_filter))
            next_predict = get_expect(dog_code_filter)
            if len(next_predict) != 0:
                #notify_dict.update({dog_code:next_predict})
                notify_dict.update({dog_code_filter+'.US':next_predict})   # Support US market fornow
                log.get().info('[%s]: %s'%(dog_code_filter, str(next_predict)))

    return notify_dict

def trade(user, q_type, house_dict, dog_opt, dog_id):
    def get_holding_by_dog_id(holding_dict, dog_id):
        for index in holding_dict:
            if index.get('Code', '') == dog_id:
                return index
        return {}
    available_cash = float(house_dict['AvailableCash'])
    holding = get_holding_by_dog_id(json.loads(house_dict['Holding'].replace("'",'"')), dog_id)
    log.get().info('[%s] holding: %s'%(dog_id, str(holding)))
    if len(holding) == 0:
        holding.update({'Quantity':0})

    for order_index in dog_opt:
        val = float(dog_opt[order_index])
        curr_share = holding.get('Quantity')
        opt_share = 0
        if order_index == 'buy':
            if curr_share == 0:
                opt_share = 1
            else:
                opt_share = curr_share * 2  # buy double
        elif order_index == 'sell':
            if (curr_share == 0):
                continue
            opt_share = curr_share // 2
        else:
            continue
        if opt_share == 0:
            log.get().info('[%s] Nothing to opt due to opt_share == 0......'%(dog_id))
            continue
        log.get().info('[%s] %s %d shares in price %.2f'%(dog_id, order_index, opt_share, val))
        
        submit_order(user, q_type, dog_id, order_index, val, opt_share)

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success...[%s]'%(py_name))

    quantitative_init(args.quantitative, args.user)
    if args.user == '':
        log.get().error('User Null')
        return 

    if not args.test:
        wait_us_market_open(log.get())

    #result = subprocess.run(["python3", "%s/../input/house.py"], capture_output=True, text=True)
    house_update(args.user)
    predict_dict = get_expect_all(args.quantitative, args.user)
    log.get().info('Predict result: %s'%(str(predict_dict)))

    house_dict = get_house_detail('%s-%s'%(args.quantitative, args.user))

    #predict_dict = {'NVDA.US':{'buy':123.45}} # test code
    #order_dest = '%s-%s'%(args.quantitative, args.user)
    # Submit order
    for index in predict_dict:
        dog_opt = predict_dict[index]
        trade(args.user, args.quantitative, house_dict, dog_opt, index)

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    parser.add_argument('--user', type=str, default='', help='')
    parser.add_argument('--quantitative', type=str, default='simulation', help='Now supported: "simulation"(default),"formal"')
    parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)
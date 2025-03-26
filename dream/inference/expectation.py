#!/bin/python3

# System lib
import os
import re
import sys
import random
import argparse
import datetime
import pandas as pd

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
from strategy import basic, get_stategy_handle
sys.path.append(r'%s/../common'%(py_dir))
from config import get_strategy, get_notify_list, get_trade_list
from database import create_if_expectation_inexist, update_expectation
from database import get_holding, get_market_by_range, get_dogname, get_avg_score
from other import wait_us_market_open, get_user_type
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

# Only for temp during simulation trade test
def merge_holding(quent_type, user_name, notify_list):
    house_holding = get_holding(get_user_type('-'))
    for index in house_holding:
        dog_code = index.get('Code')
        dog_code = dog_code[:dog_code.rfind('.US')]     # Support US market fornow
        if dog_code not in notify_list:
            if re.search(r'\d{6}', dog_code):   # Search if have number like '250117'
                #log.get().info('Detect share option[%s], skip for now'%(dog_code))
                pass
            else:
                notify_list.append(dog_code)
    return notify_list

def get_expect(dog_code):
    stategy_handle = get_stategy_handle(dog_code)
    if stategy_handle == None:
        #log.get().error('stategy_handle Null')
        return
    current_date = datetime.datetime.now().strftime('%Y%m%d')
    start_date = (datetime.datetime.now() - datetime.timedelta(days=(stategy_handle.long * 5))).strftime('%Y%m%d')
    df = get_market_by_range(dog_code, start_date, current_date)
    next_predict = stategy_handle.mean_reversion_expect(df)
    return next_predict

def get_option_notify(dog_code, next_predict):
    stategy_handle = get_stategy_handle(dog_code)
    if stategy_handle == None:
        #log.get().error('stategy_handle Null')
        return
    current_date = datetime.datetime.now().strftime('%Y%m%d')
    start_date = (datetime.datetime.now() - datetime.timedelta(days=(stategy_handle.long * 6))).strftime('%Y%m%d')
    df = get_market_by_range(dog_code, start_date, current_date)
    df = stategy_handle.mean_reversion(df)
    trades = df[df['Signal'] != 0]
    
    opt_list = []
    for i in range(len(df)):
        if df['Position'].iloc[i] > 0.9 and df['Signal'].iloc[i] == 1:
            opt_list.append(1)
        elif df['Position'].iloc[i] < -0.9 and df['Signal'].iloc[i] == -1:
            opt_list.append(-1)

    #log.get().info('opt_list[%s]'%(str(opt_list)))
    # Same opration in last reversion, then recomand to buy a option.
    continue_count = random.choices([3, 5], weights=[1, 1], k=1)[0] # ramdom get 3 or 5 countinue count...
    if len(opt_list) >= continue_count:
        opt_list = opt_list[-continue_count:]
        #log.get().info('opt_list filter[%s]'%(str(opt_list)))
        if len(set(opt_list)) == 1:     # All are the same opration
            if opt_list[0] == 1 and next_predict.get('sell', -1) != -1:     # Already buy multi times and expect to sell, means maybe top point.
                return 'Put'                                                # Then buy a Put
            if opt_list[0] == -1 and next_predict.get('buy', -1) != -1:     # Already sell multi times and expect to buy, means maybe low point.
                return 'Call'                                               # Then buy a Call
            if opt_list[0] == 1 and next_predict.get('buy', -1) != -1:      # Already buy multi times and expect to buy, means maybe Raising ahead.
                return 'Rise'                                               # Consider buy or sell manually
            if opt_list[0] == -1 and next_predict.get('sell', -1) != -1:    # Already buy multi times and expect to buy, means maybe droping ahead.
                return 'Drop'                                               # Consider buy or sell manually 
    return 'NA'


def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success...[%s]'%(py_name))

    notify_dict = {}
    notify_list = get_notify_list(args.market)
    if args.market == 'us':     # Only for temp during simulation trade test
        if not args.test:
            wait_us_market_open(log.get())
        notify_list = merge_holding('formal', 'Kanos', notify_list)
    code_name_dict = {}
    for index in notify_list:
        next_predict = get_expect(index)
        if len(next_predict) != 0:
            dog_name = get_dogname(args.market, index)
            code_name_dict.update({index:dog_name})
            option_opt = get_option_notify(index, next_predict)
            next_predict.update({'option':option_opt})
            avg_score = get_avg_score(index, 3)
            next_predict.update({'avg_score':avg_score})
            notify_dict.update({index:next_predict})
            log.get().info('[%s(%s)]: %s'%(dog_name, index, str(next_predict)))

    if len(notify_dict) != 0:
        bark_obj = notify.bark()
        content = ''
        for index in notify_dict:
            sub_content = '%s(%s)[%.3f (%.2f) %.3f]\n'%(code_name_dict.get(index, 'UnknowName'), 
                notify_dict[index].get('option', 'NA'),
                notify_dict[index].get('buy',-1),
                notify_dict[index].get('avg_score',0), 
                notify_dict[index].get('sell',-1))
            content += sub_content
            log.get().info('Ready to send content: %s'%(sub_content))
        bark_obj.send_title_content('Kanos Stock House', content)

        create_if_expectation_inexist().closeSession()
        flag = update_expectation(args.market, notify_dict)
        if not flag:
            log.get().error('Expectation update failed: %s'%(str(notify_dict)))


if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')
    parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)

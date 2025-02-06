#!/bin/python3

# System lib
import os
import sys
import argparse
import datetime
import pandas as pd

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
import akshare as ak
sys.path.append(r'%s/../common'%(py_dir))
from config import get_trade_list, get_user_config
from longport_api import quantitative_init, get_quote_context, get_option_dict_from_obj
from database import create_if_option_inexist, get_market_last
from standard import wait_us_market_open
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def get_option_list(dog_id, user):
    price_range = float(get_user_config(user, 'option', 'price_range'))
    count_limit = int(get_user_config(user, 'option', 'count_limit'))
    day_range = int(get_user_config(user, 'option', 'day_range'))

    last_price = float(get_market_last(dog_id).get('Close'))    # Now getting from database, to be consider getting from realtime data...
    lower_bound = last_price * (1.0 - price_range)
    upper_bound = last_price * (1.0 + price_range)

    ctx = get_quote_context()
    today = datetime.date.today()
    date_list = ctx.option_chain_expiry_date_list('%s.US'%(dog_id))
    interval = today + datetime.timedelta(days=day_range)   # day_range days beyond...
    filtered_dates = [d for d in date_list if d >= interval][:count_limit]     # get the first option_count date\

    option_list = []
    for date_index in filtered_dates:
        tmp_option_list = ctx.option_chain_info_by_date('%s.US'%(dog_id), date_index)
        for option_index in tmp_option_list:
            if (lower_bound > option_index.price or option_index.price > upper_bound):
                continue
            option_status = ctx.option_quote([option_index.call_symbol, option_index.put_symbol])
            for option_status_index in option_status:
                #log.get().info(option_status_index)
                temp_dict = get_option_dict_from_obj(option_status_index)
                option_list.append(temp_dict)
    return option_list

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success')

    if not args.test:
        wait_us_market_open(log.get())

    quantitative_init()

    dog_list = get_trade_list('us')
    log.get().info(dog_list)

    db = create_if_option_inexist()
    for dog_index in dog_list:
        option_list = get_option_list(dog_index, os.environ['USER_NAME'])
        for index in option_list:
            symbol = index['Symbol']
            log.get().info('Start update for[%s]:%s'%(symbol, str(index)))
            flag = db.update_option_by_symbol(symbol, index)
            if (not flag):
                log.get().error('Option update failed: %s'%(symbol))
                exit()


if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")
    
    # Append arguments
    parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

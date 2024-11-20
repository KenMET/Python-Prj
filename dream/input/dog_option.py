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
from config import get_trade_list
from longport_api import quantitative_init, get_quote_context
from database import create_if_option_inexist
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def get_option_list(dog_id, day_range, option_count):
    ctx = get_quote_context()
    today = datetime.date.today()
    date_list = ctx.option_chain_expiry_date_list('%s.US'%(dog_id))
    interval = today + datetime.timedelta(days=day_range)                       # day_range days beyond...
    filtered_dates = [d for d in date_list if d >= interval][:option_count]     # get the first option_count date\
    option_list = []
    for date_index in filtered_dates:
        tmp_option_list = ctx.option_chain_info_by_date('%s.US'%(dog_id), date_index)
        for option_index in tmp_option_list:
            option_status = ctx.option_quote([option_index.call_symbol, option_index.put_symbol])
            temp_dict = {
                'CodeDatePrice': '%s-%s-%s'%(dog_id, date_index.strftime('%Y%m%d'), str(option_index.price)),
                'CallSymbol': option_index.call_symbol, 
                'PutSymbol': option_index.put_symbol, 
                'Standard': option_index.standard, 
            }
            log.get().info(temp_dict)
            log.get().info(option_status)
            exit()
            option_list.append(temp_dict)
    return option_list

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success')

    quantitative_init(args.quantitative, 'Kanos')

    dog_list = get_trade_list('us')
    log.get().info(dog_list)

    db = create_if_option_inexist()
    for dog_index in dog_list:
        log.get().info('################################################################')
        option_list = get_option_list(dog_index, 30*3, 5)


if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")
    
    # Append arguments
    parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')
    parser.add_argument('--quantitative', type=str, default='simulation', help='Now supported: "simulation"(default),"formal"')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

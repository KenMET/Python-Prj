#!/bin/python3

# System lib
import os
import sys
import json
import random
import hashlib
import argparse
import datetime, time
import re
import numpy as np
import pandas as pd
from decimal import Decimal

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
import adata
import akshare as ak
import longport.openapi
from strategy import get_strategy, basic
sys.path.append(r'%s/../input'%(py_dir))
from dream_house import get_house_setup_from_config, get_holding
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_dream_dog as dbdd
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/xml_operator'%(py_dir))
import xml_operator as xo
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log


def get_market_by_range(target, start, end):
    db = dbdd.db('dream_dog')
    ret = db.query_dog_markey_by_daterange(target, start, end)
    df = pd.DataFrame([db.get_dict_from_obj(i) for i in ret])
    
    # Make sure date soted
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')           # 确保 Close 列为数值类型

    return df

def get_stategy_handle(target):
    strategy_dict = get_strategy(target)
    strategy_type = strategy_dict['class']
    if strategy_type == 'basic':
        short = int(strategy_dict['short_window'])
        long = int(strategy_dict['long_window'])
        th = float(strategy_dict['threshold'])
        trade_interval = int(strategy_dict['cool_down_period'])
        stategy_handle = basic(short, long, th, trade_interval)
    elif strategy_type == 'xxxx':   # to be update
        pass
    return stategy_handle

def pridct_next(quent_type, user_name):
    house_name = '%s-%s'%(quent_type, user_name)
    house_holding = get_holding(house_name)
    log.get(py_name).info(house_holding)

    notify_dict = {}
    for hold_index in house_holding:
        dog_code = hold_index.get('Code')
        dog_code = dog_code[:dog_code.rfind('.US')]     # Support US market fornow
        if re.search(r'\d{6}', dog_code):   # Search if have number like '250117'
            log.get(py_name).info('Detect share option[%s]'%(dog_code))
        else:
            stategy_handle = get_stategy_handle(dog_code)
            if stategy_handle == None:
                log.get(py_name).error('stategy_handle Null')
                return
            current_date = datetime.datetime.now().strftime('%Y%m%d')
            start_date = (datetime.datetime.now() - datetime.timedelta(days=(stategy_handle.long * 2))).strftime('%Y%m%d')
            df = get_market_by_range(dog_code, start_date, current_date)
            next_predict = stategy_handle.mean_reversion_expect(df)
            if len(next_predict) != 0:
                notify_dict.update({dog_code:next_predict})
                log.get(py_name).info('[%s]: %s'%(dog_code, str(next_predict)))
    if len(notify_dict) != 0:
        bark_obj = notify.bark()
        content = ''
        for index in notify_dict:
            content += '%s: [0,%.3f]&[%.2f,+∞]\n'%(index, 1.2, 8.8)
        bark_obj.send_title_content('Kanos Stock House', content)


def main(args):
    log.init(py_dir, py_name, log_mode='w', log_level='info', console_enable=True)
    log.get(py_name).info('Logger Creat Success...[%s]'%(py_name))
    
    quantitative_type = ['simulation', 'formal']
    house_dict = get_house_setup_from_config()
    for user_name in house_dict:
        quent_type = house_dict[user_name].get('quent_type', 'simulation')
        if quent_type == 'both':
            for q_type in quantitative_type:
                pridct_next(q_type, user_name)
        else:
            pridct_next(quent_type, user_name)


if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    parser.add_argument('--start', type=str, default='', help='Start Date, for example: 20241001')
    parser.add_argument('--end', type=str, default='', help='End Date, null as today')
    #parser.add_argument('--target', type=str, default='', help='Backtest dog name')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)


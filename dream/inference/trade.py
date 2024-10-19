#!/bin/python3

# System lib
import os
import sys
import json
import random
import hashlib
import argparse
import subprocess
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
from dream_house import get_house_setup_from_config, get_holding, get_house
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_dream_dog as dbdd
import db_dream_secret as dbds
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/xml_operator'%(py_dir))
import xml_operator as xo
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def quantitative_init(quant_type, user):
    db = dbds.db('dream_sentiment')
    if (not db.is_table_exist()):
        #log.get(py_name).info('Quantitative table not exist, new a table...')
        db.create_secret_table()
    res = db.query_secret_by_type(quant_type, user)
    if len(res) != 1:
        return
    os.environ['LONGPORT_APP_KEY'] = res[0].App_Key
    os.environ['LONGPORT_APP_SECRET'] = res[0].App_Secret
    os.environ['LONGPORT_ACCESS_TOKEN'] = res[0].Access_Token

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

    notify_dict = {}
    for hold_index in house_holding:
        dog_code = hold_index.get('Code')
        dog_code_filter = dog_code[:dog_code.rfind('.US')]     # Support US market fornow
        if re.search(r'\d{6}', dog_code_filter):   # Search if have number like '250117'
            log.get(py_name).info('Detect share option[%s]'%(dog_code_filter))
        else:
            stategy_handle = get_stategy_handle(dog_code_filter)
            if stategy_handle == None:
                log.get(py_name).error('stategy_handle Null')
                return {}
            current_date = datetime.datetime.now().strftime('%Y%m%d')
            start_date = (datetime.datetime.now() - datetime.timedelta(days=(stategy_handle.long * 2))).strftime('%Y%m%d')
            df = get_market_by_range(dog_code_filter, start_date, current_date)
            next_predict = stategy_handle.mean_reversion_expect(df)
            if len(next_predict) != 0:
                notify_dict.update({dog_code:next_predict})
                #log.get(py_name).info('[%s]: %s'%(dog_code, str(next_predict)))
    return notify_dict

def get_holding_by_dog_id(holding_dict, dog_id):
    for index in holding_dict:
        if index.get('Code', '') == dog_id:
            return index
    return {}

def trade(ctx, house_dict, dog_opt, dog_id):
    available_cash = float(house_dict['AvailableCash'])
    holding = get_holding_by_dog_id(json.loads(house_dict['Holding'].replace("'",'"')), dog_id)
    log.get(py_name).info('[%s] holding: %s'%(dog_id, str(holding)))

    for order_index in dog_opt:
        val = float(dog_opt[order_index])
        curr_share = holding.get('Quantity')
        opt_share = 0
        if order_index == 'buy':
            if curr_share == 0:
                opt_share = 1
            else:
                opt_share = curr_share * 2
            log.get(py_name).info('[%s] Buy %d %.2f'%(dog_id, opt_share, val))
            resp = ctx.submit_order(symbol = dog_id,
                side = longport.openapi.OrderSide.Buy,
                order_type = longport.openapi.OrderType.LO,
                submitted_price = round(val, 2),
                submitted_quantity = int(opt_share),
                time_in_force = longport.openapi.TimeInForceType.Day,
                remark = "Buy",
            )
        elif order_index == 'sell':
            if (curr_share == 0):
                continue
            opt_share = curr_share // 2
            log.get(py_name).info('[%s] Sell %d %.2f'%(dog_id, opt_share, val))
            resp = ctx.submit_order(symbol = dog_id,
                side = longport.openapi.OrderSide.Sell,
                order_type = longport.openapi.OrderType.LO,
                submitted_price = round(val, 2),
                submitted_quantity = int(opt_share),
                time_in_force = longport.openapi.TimeInForceType.Day,
                remark = "Sell",
            )



def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get(py_name).info('Logger Creat Success...[%s]'%(py_name))
    exit()
    if args.user == '':
        log.get(py_name).error('User Null')
        return 

    result = subprocess.run(["python3", "%s/../input/dream_house.py"], capture_output=True, text=True)
    quantitative_init(args.quantitative, args.user)
    predict_dict = pridct_next(args.quantitative, args.user)
    log.get(py_name).info(predict_dict)

    house_dict = get_house('%s-%s'%(args.quantitative, args.user))

    ctx = longport.openapi.TradeContext(longport.openapi.Config.from_env())
    # Submit order
    for index in predict_dict:
        dog_opt = predict_dict[index]
        trade(ctx, house_dict, dog_opt, index)

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    parser.add_argument('--user', type=str, default='', help='')
    parser.add_argument('--quantitative', type=str, default='simulation', help='Now supported: "simulation"(default),"formal"')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)
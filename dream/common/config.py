#!/bin/python3

# System lib
import os
import sys
import json
import random
import datetime, time
import numpy as np
import pandas as pd
from decimal import Decimal

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../../common_api/xml_operator'%(py_dir))
import xml_operator as xo
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log


def config(config_name):
    cfg = xo.operator('%s/../config/%s.xml'%(py_dir, config_name))
    cfg_dict = cfg.walk_node(cfg.root_node)
    return cfg_dict

def get_cat(market='cn'):
    cfg = config('animal')
    tmp_list = cfg.get('cat_%s_list'%(market), {}).get('id', [])
    if type(tmp_list) == type(''):
        tmp_list = [tmp_list, ]
    return tmp_list

def get_dog(market='cn'):
    cfg = config('animal')
    tmp_list = cfg.get('dog_%s_list'%(market), {}).get('id', [])
    if type(tmp_list) == type(''):
        tmp_list = [tmp_list, ]
    return tmp_list

def get_trade_list(market='cn'):
    cfg = config('animal')
    tmp_list = cfg.get('trade_list', {}).get(market, {}).get('id', [])
    if type(tmp_list) == type(''):
        tmp_list = [tmp_list, ]
    return tmp_list

def get_notify_list(market='cn'):
    cfg = config('animal')
    tmp_list = cfg.get('notify_list', {}).get(market, {}).get('id', [])
    if type(tmp_list) == type(''):
        tmp_list = [tmp_list, ]
    return tmp_list

def get_strategy(id):
    cfg = config('strategy')
    long_tmp = cfg.get('long_strategy', {})
    short_tmp = cfg.get('short_strategy', {})

    # Default short/long-term trade strategy
    strategy_dict = {}
    strategy_dict.update({'long':{'class':'mean_reversion', 'detail':cfg.get('mean_reversion', {}).get('config_0', {})}})
    strategy_dict.update({'short':{'class':'bollinger', 'detail':cfg.get('bollinger', {}).get('config_0', {})}})

    strategy_type = ''
    strategy_item = ''
    for index in long_tmp:
        if index == id:
            strategy_type = long_tmp[index].get('type', '')
            strategy_item = long_tmp[index].get('item', '')
            break
    if strategy_type == '' or strategy_item == '':
        return strategy_dict
    detail = cfg.get(strategy_type, {}).get(strategy_item, {})
    tmp = {'class':strategy_type, 'detail':detail}
    strategy_dict.update({'long':tmp})

    strategy_type = ''
    strategy_item = ''
    for index in short_tmp:
        if index == id:
            strategy_type = short_tmp[index].get('type', '')
            strategy_item = short_tmp[index].get('item', '')
            break
    if strategy_type == '' or strategy_item == '':
        return strategy_dict
    detail = cfg.get(strategy_type, {}).get(strategy_item, {})
    tmp = {'class':strategy_type, 'detail':detail}
    strategy_dict.update({'short':tmp})

    return strategy_dict

def get_global_config(config_name):
    cfg = config('user')
    return cfg.get('global', {}).get(config_name, None)

def get_user_config(user, class_name, config_name):
    cfg = config('user')
    return cfg.get(user, {}).get(class_name, {}).get(config_name, None)

def get_short_trade_list(user, market='us'):
    tmp_list = get_user_config(user, 'short_term_trade_list', market).get('id', [])
    if type(tmp_list) == type(''):
        tmp_list = [tmp_list, ]
    return tmp_list

def get_adata_key():
    cfg = config('user')
    return cfg.get('sentiment_key', {}).get('key', {})

def get_adata_key():
    cfg = config('user')
    return cfg.get('sentiment_key', {}).get('key', {})

def main():
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success...')

    
    log.get().info(get_short_trade_list('kanos'))


if __name__ == '__main__':
    main()




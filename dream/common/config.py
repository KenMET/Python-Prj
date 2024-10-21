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

def get_dog(market='cn_a'):
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
    tmp = cfg.get('strategy', {})
    strategy_type = ''
    strategy_item = ''
    default_config = {'class':'basic'}
    default_config.update(cfg.get('mean_reversion', {}).get('config_0', {}))

    for index in tmp:
        if index == id:
            strategy_type = tmp[index].get('type', '')
            strategy_item = tmp[index].get('item', '')
    if strategy_type == '' or strategy_item == '':
        return default_config

    tmp = cfg.get(strategy_type, {}).get(strategy_item, {})
    if strategy_type == 'mean_reversion':
        tmp.update({'class':'basic'})
    return tmp

def get_house(user=None):
    cfg = config('user')
    if user == None:
        return cfg
    return cfg.get(user, {})

def main():
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success...')

    
    log.get().info(get_strategy('NVDA'))


if __name__ == '__main__':
    main()




#!/bin/python3

# System lib
import os
import sys
import ast
import json
import random
import argparse
import datetime, time

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
import pandas as pd
from decimal import Decimal
import adata
import akshare as ak
import longport.openapi
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_dream_dog as dbdd
import db_dream_dog_info as dbddi
import db_dream_secret as dbds
import db_dream_account as dbda
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log
sys.path.append(r'%s/../../common_api/xml_operator'%(py_dir))
import xml_operator as xo

def get_config_dict():
    file_name = '%s/config.xml'%(py_dir)
    cfg = xo.operator(file_name)
    cfg_dict = cfg.walk_node(cfg.root_node)
    return cfg_dict

def get_house_list_from_config():     # From config file(default)
    cfg_dict = get_config_dict()
    house_list = cfg_dict.get('house_config', {}).get('id', [])
    if type(house_list) == type(''):
        house_list = [house_list, ]
    return house_list

def quantitative_init(quant_type, user):
    db = dbds.db('dream_sentiment')
    if (not db.is_table_exist()):
        log.get(py_name).info('Quantitative table not exist, new a table...')
        db.create_secret_table()
    res = db.query_secret_by_type(quant_type, user)
    if len(res) != 1:
        return
    os.environ['LONGPORT_APP_KEY'] = res[0].App_Key
    os.environ['LONGPORT_APP_SECRET'] = res[0].App_Secret
    os.environ['LONGPORT_ACCESS_TOKEN'] = res[0].Access_Token

def house_update(name):
    db = dbda.db('dream_sentiment')
    if (not db.is_table_exist()):      # New a table to insert
        log.get(py_name).info('House not exist, new a table...')
        db.create_dog_house_table()
    trade_ctx = longport.openapi.TradeContext(longport.openapi.Config.from_env())
    resp = trade_ctx.account_balance(currency='USD')
    if len(resp) != 1:
        log.get(py_name).info('Account Balance exception: %s'%(str(resp)))
        return
    house = resp[0]
    if len(house.cash_infos) != 1:
        log.get(py_name).info('Account Balance Cash Infos exception: %s'%(str(resp)))
        return
    house_cash_infos = house.cash_infos[0]
    house_dict = {
        'Account':name,
        'NetAssets':house.net_assets,
        'TotalCash':house.total_cash,
        'MaxFinanceAmount':house.max_finance_amount,
        'RiskLevel':house.risk_level,
        'BuyPower':house.buy_power,
        'FrozenCash':house_cash_infos.frozen_cash,
        'SettlingCash':house_cash_infos.settling_cash,
        'AvailableCash':house_cash_infos.available_cash,
        'WithdrawCash':house_cash_infos.withdraw_cash,
    }
    resp = trade_ctx.stock_positions()
    if len(resp.channels) != 1:
        log.get(py_name).info('Stock Positions exception: %s'%(str(resp)))
        return
    positions = resp.channels[0].positions
    holding_list = []
    for index in positions:
        holding_list.append({'Code':index.symbol,'Quantity':int(index.init_quantity),'CostPrice':float(index.cost_price)})
    house_dict.update({'Holding':str(holding_list)})
    db.update_house_by_name(name, house_dict)

def get_house(name):
    db = dbda.db('dream_sentiment')
    temp = db.query_house_by_name(name)
    if len(temp) != 1:
        log.get(py_name).info('House get exception: %s'%(name))
        return
    return db.get_dict_from_obj(temp[0])

def get_holding(name):
    db = dbda.db('dream_sentiment')
    temp = db.query_house_by_name(name)
    if len(temp) != 1:
        log.get(py_name).info('House get exception: %s'%(name))
        return
    account_dict = db.get_dict_from_obj(temp[0])
    return ast.literal_eval(account_dict['Holding'])


def main(args):
    log.init(py_dir, py_name, log_mode='w', log_level='info', console_enable=True)
    log.get(py_name).info('Logger Creat Success')

    quantitative_type = ['simulation', 'formal']
    house_list = get_house_list_from_config()
    for index in house_list:
        if args.quantitative != '':
            quantitative_init(args.quantitative, index)
            house_name = '%s-%s'%(args.quantitative, index)
            log.get(py_name).info('start update house: %s'%(house_name))
            house_update(house_name)
            house = get_house(house_name)
            house_holding = get_holding(house_name)
            log.get(py_name).info(house)
            log.get(py_name).info(house_holding)
        else:
            for q_type in quantitative_type:
                quantitative_init(q_type, index)
                house_name = '%s-%s'%(q_type, index)
                log.get(py_name).info('start update house: %s'%(house_name))
                house_update(house_name)
                house = get_house(house_name)
                house_holding = get_holding(house_name)
                log.get(py_name).info(house)
                log.get(py_name).info(house_holding)

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A inference module for dog")
    
    # Append arguments
    parser.add_argument('--quantitative', type=str, default='', help='Now supported: "simulation"(default),"formal"')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

#!/bin/python3

# System lib
import os
import sys
import ast
import argparse

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_dream_account as dbda
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log
sys.path.append(r'%s/../common'%(py_dir))
from config import get_house
from longport_api import quantitative_init, get_trade_context
from database import create_if_house_inexist, get_house_detail, get_holding

def house_update(name):
    db = create_if_house_inexist()
    trade_ctx = get_trade_context()
    resp = trade_ctx.account_balance(currency='USD')
    if len(resp) != 1:
        log.get().info('Account Balance exception: %s'%(str(resp)))
        return
    house = resp[0]
    if len(house.cash_infos) != 1:
        log.get().info('Account Balance Cash Infos exception: %s'%(str(resp)))
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
        log.get().info('Stock Positions exception: %s'%(str(resp)))
        return
    positions = resp.channels[0].positions
    holding_list = []
    for index in positions:
        holding_list.append({'Code':index.symbol,'Quantity':int(index.init_quantity),'CostPrice':float(index.cost_price)})
    house_dict.update({'Holding':str(holding_list)})
    db.update_house_by_name(name, house_dict)
    log.get().info('House updated for: %s'%(name))

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success')

    quantitative_type = ['simulation', 'formal']
    house_dict = get_house()
    for user_name in house_dict:
        quent_type = house_dict[user_name].get('quent_type', 'simulation')
        if quent_type == 'both':
            for q_type in quantitative_type:
                quantitative_init(q_type, user_name)
                house_name = '%s-%s'%(q_type, user_name)
                log.get().info('start update house: %s'%(house_name))
                house_update(house_name)
                house = get_house_detail(house_name)
                house_holding = get_holding(house_name)
                log.get().info(house)
                log.get().info(house_holding)
        else:
            quantitative_init(quent_type, user_name)
            house_name = '%s-%s'%(quent_type, user_name)
            log.get().info('start update house: %s'%(house_name))
            house_update(house_name)
            house = get_house_detail(house_name)
            house_holding = get_holding(house_name)
            log.get().info(house)
            log.get(py_name).info(house_holding)

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A inference module for dog")
    
    # Append arguments
    # parser.add_argument('--quantitative', type=str, default='', help='Now supported: "simulation"(default),"formal"')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

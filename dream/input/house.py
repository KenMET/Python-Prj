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
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../common'%(py_dir))
from longport_api import quantitative_init, get_trade_context
from database import create_if_house_inexist, get_house_detail, get_holding, get_secret_detail
from other import wait_us_market_open, get_user_type
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log
log_name = '%s_%s'%(py_name, get_user_type('_'))


def house_update(name):
    db = create_if_house_inexist()
    trade_ctx = get_trade_context()
    resp = trade_ctx.account_balance(currency='USD')
    if len(resp) != 1:
        log.get(log_name).info('Account Balance exception: %s'%(str(resp)))
        db.closeSession()
        return
    house = resp[0]
    if len(house.cash_infos) != 1:
        log.get(log_name).info('Account Balance Cash Infos exception: %s'%(str(resp)))
        db.closeSession()
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
        log.get(log_name).info('Stock Positions exception: %s'%(str(resp)))
        db.closeSession()
        return
    positions = resp.channels[0].positions
    holding_list = []
    for index in positions:
        holding_list.append({'Code':index.symbol,'Quantity':int(index.init_quantity),'CostPrice':float(index.cost_price)})
    house_dict.update({'Holding':str(holding_list)})
    db.update_house_by_name(name, house_dict)
    log.get(log_name).info('House updated for: %s'%(name))
    db.closeSession()

# Not support for multiple user for now...
def main(args):
    log.init('%s/../log'%(py_dir), log_name, log_mode='w', log_level='info', console_enable=True)
    log.get(log_name).info('Logger[%s] Creat Success'%(log_name))

    if not args.test:
        wait_us_market_open(log.get(log_name))

    user = os.environ['USER_NAME']
    quent_type = os.environ['USER_TYPE']
    try:
        quantitative_init()
        house_name = get_user_type('-')
        log.get(log_name).info('start update [%s]'%(get_user_type('-')))
        house_update(house_name)
        house = get_house_detail(house_name)
        house_holding = get_holding(house_name)
        log.get(log_name).info(house)
        log.get(py_name).info(house_holding)
    except:
        log.get(log_name).error('House Update', '[%s] update fail, please check if token expired.'%(get_user_type('-')))
        bark_obj = notify.bark()
        flag = bark_obj.send_title_content('House Update', '[%s] update fail, please check if token expired.'%(get_user_type('-')))

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A inference module for dog")
    
    # Append arguments
    # parser.add_argument('--quantitative', type=str, default='', help='Now supported: "simulation"(default),"formal"')
    parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

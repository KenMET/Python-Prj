#!/bin/python3

# System lib
import os
import sys
import json
import random
import hashlib
import argparse
import datetime, time
import pandas as pd
from decimal import Decimal

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
import adata
import akshare as ak
import longport.openapi
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_cat as dbc
import db_dream_dog as dbdd
import db_dream_dog_info as dbddi
import db_dream_secret as dbds
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/xml_operator'%(py_dir))
import xml_operator as xo
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def sanity_info(db, table_name):
    pass

def sanity_market(db, table_name):
    dog_id = table_name[table_name.rfind('_')+1:]
    temp_obj = db.query_dog_market_last(dog_id)
    if (temp_obj == None):
        log.get(py_name).info('Market Sanity None:[%s]'%(dog_id))
        return False
    temp_dict = db.get_dict_from_obj(temp_obj)
    temp_date = temp_dict['Date']

    today = datetime.date.today()
    some_days_ago = today - datetime.timedelta(days=10)
    if some_days_ago <= temp_date <= today:
        #log.get(py_name).info('Market Sanity Success: [%s]'%(dog_id))
        return True
    else:
        log.get(py_name).info('Market Sanity Failed:[%s]'%(dog_id))
        #db.dropTable(table_name)
        return False

def main(args):
    log.init(py_dir, py_name, log_mode='w', log_level='info', console_enable=True)
    log.get(py_name).info('Logger Creat Success...')
    bark_obj = notify.bark()

    fail_list = []
    db = dbdd.db('dream_dog')
    table_list = db.queryTable()
    for index in table_list:
        if index.find('info') > 0:
            sanity_info(db, index)
        elif index.find('market') > 0:
            flag = sanity_market(db, index)
            if (not flag):
                fail_list.append(index)
    if len(fail_list) != 0:
        log.get(py_name).info('Failed list: %s'%(fail_list))
        flag = bark_obj.send_title_content('Market Sanity', 'Failed list: %s'%(fail_list))
    else:
        log.get(py_name).info('All market DB works normal')
        flag = bark_obj.send_title_content('Market Sanity', 'All market DB works normal')
    log.get(py_name).info('Bark Notification Result[%s]'%(str(flag)))

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")
    
    # Append arguments
    parser.add_argument('--market', type=str, default='cn_a', help='Now supported: "cn_a"(default),"us"')
    parser.add_argument('--quantitative', type=str, default='simulation', help='Now supported: "simulation"(default),"formal"')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)


#!/bin/python3

# System lib
import ast
import os, sys
import argparse
import pandas as pd

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
import akshare as ak
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_dream_dog as dbdd
import db_dream_secret as dbds
import db_dream_account as dbda
import db_dream_dog_info as dbddi
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log


def create_and_clear_info(market):
    db = dbddi.db('dream_dog')
    if (not db.is_table_exist(market)):
        log.get().info('%s dog info table not exist, create...'%(market))
        db.create_dog_info_table(market)
    db.delete_dog_all(market)
    return db

def get_us_fullcode(market, dog_id):
    db_info = dbddi.db('dream_dog')
    res = db_info.query_dog_fullcode_by_code(market, dog_id)
    if len(res) == 0:
        log.get().error('Dog not found [%s]'%(dog_id))
        return dog_id 
    elif len(res) != 1:
        tmp_list = [i.Code for i in res]
        dog_full_code = [item for item in tmp_list if item.endswith('.' + dog_id)][0]
    else:
        dog_full_code = res[0].Code
    return dog_full_code

# True:     inexist
# False:    exist
def create_if_market_inexist(name):
    db = dbdd.db('dream_dog')
    if (not db.is_table_exist(name)):      # New a table to insert
        log.get().info('Dog[%s] not exist, new a table...'%(name))
        db.create_dog_market_table(name)
        return db, True
    return db, False

def create_if_house_inexist():
    db = dbda.db('dream_sentiment')
    if (not db.is_table_exist()):      # New a table to insert
        log.get().info('House not exist, new a table...')
        db.create_dog_house_table()
    return db 

def get_house_detail(name):
    db = dbda.db('dream_sentiment')
    temp = db.query_house_by_name(name)
    if len(temp) != 1:
        #log.get().info('House get exception: %s'%(name))
        return
    return db.get_dict_from_obj(temp[0])

def get_holding(name):
    db = dbda.db('dream_sentiment')
    temp = db.query_house_by_name(name)
    if len(temp) != 1:
        #log.get().info('House get exception: %s'%(name))
        return
    account_dict = db.get_dict_from_obj(temp[0])
    return ast.literal_eval(account_dict['Holding'])

def get_market_by_range(target, start, end):
    db = dbdd.db('dream_dog')
    ret = db.query_dog_markey_by_daterange(target, start, end)
    df = pd.DataFrame([db.get_dict_from_obj(i) for i in ret])
    
    # Make sure date soted
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')           # 确保 Close 列为数值类型

    return df

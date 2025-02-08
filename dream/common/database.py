#!/bin/python3

# System lib
import ast
import json
import os, sys
import argparse
import datetime
import pandas as pd

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
import akshare as ak
from other import datetime_converter, get_user_type
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_dream_dog as dbdd
import db_dream_order as dbdo
import db_dream_secret as dbds
import db_dream_option as dbdop
import db_dream_account as dbda
import db_dream_realtime as dbdr
import db_dream_dog_info as dbddi
import db_dream_sentiment as dbdst
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log


def create_and_clear_info(market):
    db = dbddi.db('dream_dog')
    if (not db.is_table_exist(market)):
        #log.get().info('%s dog info table not exist, create...'%(market))
        db.create_dog_info_table(market)
    db.delete_dog_all(market)
    return db

# True:     inexist
# False:    exist
def create_if_market_inexist(name):
    db = dbdd.db('dream_dog')
    if (not db.is_table_exist(name)):      # New a table to insert
        #log.get().info('Dog[%s] not exist, new a table...'%(name))
        db.create_dog_market_table(name)
        return db, True
    return db, False

def create_if_house_inexist():
    db = dbda.db('dream_user')
    if (not db.is_table_exist()):      # New a table to insert
        #log.get().info('House not exist, new a table[house]...')
        db.create_house_table()
    return db 

def create_if_order_inexist(order_dest):
    db = dbdo.db('dream_user')
    if (not db.is_table_exist(order_dest)):      # New a table to insert
        #log.get().info('Order not exist, new a table[%s]...'%('order_%s'%(order_dest)))
        db.create_order_table(order_dest)
    return db 

def create_if_sentiment_inexist():
    db = dbdst.db('dream_dog')
    if (not db.is_table_exist()):      # New a table to insert
        #log.get().info('Sentiment not exist, new a table[sentiment]...')
        db.create_sentiment_table()
    return db 

def create_if_option_inexist():
    db = dbdop.db('dream_dog')
    if (not db.is_table_exist()):      # New a table to insert
        #log.get().info('Option not exist, new a table[dog_option]...')
        db.create_dog_option_table()
    return db 

def create_if_realtime_inexist():
    db = dbdr.db('dream_dog')
    if (not db.is_param_table_exist()):      # New a table to insert
        #log.get().info('Realtime Parameters not exist, new a table[realtime_parameters]...')
        db.create_realtime_param_table()
    if (not db.is_dog_table_exist()):      # New a table to insert
        #log.get().info('Realtime Dog not exist, new a table[realtime_dog]...')
        db.create_realtime_dog_table()
    return db

def get_fullcode(market, dog_id):
    db_info = dbddi.db('dream_dog')
    res = db_info.query_dog_by_code(market, dog_id)
    if len(res) == 0:
        #log.get().error('Dog not found [%s]'%(dog_id))
        return dog_id 
    elif len(res) != 1:
        tmp_list = [i.Code for i in res]
        dog_full_code = [item for item in tmp_list if item.endswith('.' + dog_id)][0]
    else:
        dog_full_code = res[0].Code
    return dog_full_code

def get_dogname(market, dog_id):
    db_info = dbddi.db('dream_dog')
    res = db_info.query_dog_by_code(market, dog_id)
    if len(res) == 0:
        #log.get().error('Dog not found [%s]'%(dog_id))
        return dog_id 
    elif len(res) != 1:
        tmp_list = [i.Name for i in res]
        dog_name = [item for item in tmp_list if item.endswith('.' + dog_id)][0]
    else:
        dog_name = res[0].Name
    return dog_name

def get_house_detail(name):
    db = dbda.db('dream_user')
    if (not db.is_table_exist()):      # New a table to insert
        #log.get().info('House not exist, new a table[house]...')
        db.create_house_table()
    temp = db.query_house_by_name(name)
    if len(temp) != 1:
        #log.get().info('House get exception: %s'%(name))
        return
    return db.get_dict_from_obj(temp[0])

def get_secret_detail():
    db = dbds.db('dream_user')
    temp = db.query_all_secret()
    secret_list = []
    for index in temp:
        full = index.Type.split('-')
        temp_secret = {
            'user': full[0],
            'type': full[1],
        }
        secret_list.append(temp_secret)
    return secret_list

def get_holding(name):
    db = dbda.db('dream_user')
    temp = db.query_house_by_name(name)
    if len(temp) != 1:
        #log.get().info('House get exception: %s'%(name))
        return
    account_dict = db.get_dict_from_obj(temp[0])
    return ast.literal_eval(account_dict['Holding'])

def get_open_order(user, q_type):
    db = dbdo.db('dream_user')
    order_dest = get_user_type('-')
    if (not db.is_table_exist(order_dest)):      # New a table to insert
        #log.get().info('Order not exist, new a table[%s]...'%('order_%s'%(order_dest)))
        db.create_order_table(order_dest)
        return []
    temp_list = db.query_order_opened(order_dest)
    return [db.get_dict_from_obj(i) for i in temp_list] 

def get_market_last(target):
    db = dbdd.db('dream_dog')
    ret = db.query_dog_market_last(target)
    return db.get_dict_from_obj(ret)

def get_market_by_range(target, start, end):
    db = dbdd.db('dream_dog')
    ret = db.query_dog_markey_by_daterange(target, start, end)
    df = pd.DataFrame([db.get_dict_from_obj(i) for i in ret])
    
    # Make sure date soted
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')           # 确保 Close 列为数值类型

    return df

def get_avg_score(target, last_n_days):
    db = dbdst.db('dream_dog')
    current_date = datetime.datetime.now()
    start_date = (current_date - datetime.timedelta(days=last_n_days))
    ret = db.query_sentiment_by_id_date(target, start_date, current_date)
    score_list = []
    for index in ret:
        tmp_dict = db.get_dict_from_obj(index)
        score_list.append(float(tmp_dict.get('Score')))
    if len(score_list) == 0:
        return 0.0
    sorted_score_list = sorted(score_list)
    remove_min_max_count = int(len(score_list) * 0.1)     # remove 10%(min&max) of sentiment length
    trimmed_score = sorted_score_list[remove_min_max_count:-remove_min_max_count]
    if len(trimmed_score) == 0:
        return 0.0
    #log.get().info(trimmed_score)
    score_avg = sum(trimmed_score) / len(trimmed_score)
    #log.get().info('Score Avg[%s]: %.2f'%(target, score_avg))
    return score_avg

def get_registered_dog():
    db = dbdr.db('dream_dog')
    ret = db.query_param_by_symbol('registered')
    return json.loads(db.get_dict_from_obj(ret[0]).get('Content'))

def get_registered_time(dog_id):
    db = dbdr.db('dream_dog')
    ret = db.query_param_by_symbol('registered')
    return json.loads(db.get_dict_from_obj(ret[0]).get('Content')).get(dog_id)

def update_registered_time(dog_id):
    db = dbdr.db('dream_dog')
    content_dict = get_registered_dog()
    dog_tmp_dict = content_dict.get(dog_id, {})
    last_time = datetime.datetime.now()
    dog_tmp_dict.update({'time':last_time})
    content_dict.update({dog_id:dog_tmp_dict})
    symbol_dict = {
        'Symbol': 'registered',
        'Content': json.dumps(content_dict, default=datetime_converter)
    }
    return db.update_param_by_symbol('registered', symbol_dict), last_time

def del_registered_dog(dog_id):
    db = dbdr.db('dream_dog')
    content_dict = get_registered_dog()
    del content_dict[dog_id]
    symbol_dict = {
        'Symbol': 'registered',
        'Content': json.dumps(content_dict, default=datetime_converter)
    }
    return db.update_param_by_symbol('registered', symbol_dict)

def get_dog_realtime(dog_id, last_min=0):     # last_min == -1 mean all need to be return
    db = dbdr.db('dream_dog')
    ret = db.query_sharing_by_dog(dog_id)
    temp_list = [db.get_dict_from_obj(n) for n in ret]
    if last_min == 0:
        return temp_list
    result = []
    for entry in temp_list:
        dog_time_str = entry['DogTime'].split('-')[1]  # '20250207174225'
        dog_time = datetime.datetime.strptime(dog_time_str, '%Y%m%d%H%M%S')
        if (datetime.datetime.now() - dog_time) <= datetime.timedelta(minutes=int(last_min)):
            result.append(entry)
    return result

def del_dog_realtime(dog_id):     # last_min == -1 mean all need to be return
    db = dbdr.db('dream_dog')
    if db.is_dog_exist(dog_id):
        return db.del_sharing_by_dogtime(dog_id)
    return True

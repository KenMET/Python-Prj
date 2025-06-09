#!/bin/python3

# System lib
import ast
import json
import time
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
import db_dream_expectation as dbde
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

def create_if_expectation_inexist():
    db = dbde.db('dream_dog')
    if (not db.is_table_exist()):      # New a table to insert
        #log.get().info('Expectation not exist, new a table[dog_expectation]...')
        db.create_expectation_table()
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
    db = dbddi.db('dream_dog')
    res = db.query_dog_by_code(market, dog_id)
    if len(res) == 0:
        #log.get().error('Dog not found [%s]'%(dog_id))
        db.closeSession()
        return dog_id 
    elif len(res) != 1:
        tmp_list = [i.Code for i in res]
        dog_full_code_list = [item for item in tmp_list if item.endswith('.' + dog_id)]
        if len(dog_full_code_list) > 0:
            dog_full_code = dog_full_code_list[0]
        else:
            db.closeSession()
            return dog_id
    else:
        dog_full_code = res[0].Code
        if not dog_full_code.endswith('.' + dog_id):
            db.closeSession()
            return dog_id
    db.closeSession()
    return dog_full_code

def get_dogname(market, dog_id):
    db = dbddi.db('dream_dog')
    res = db.query_dog_by_code(market, dog_id)
    if len(res) == 0:
        #log.get().error('Dog not found [%s]'%(dog_id))
        db.closeSession()
        return dog_id 
    elif len(res) != 1:
        tmp_list = [i.Name for i in res]
        dog_name_list = [item for item in tmp_list if item.endswith('.' + dog_id)]
        if len(dog_name_list) > 0:
            dog_name = dog_name_list[0]
        else:
            db.closeSession()
            return dog_id
    else:
        dog_name = res[0].Name
    db.closeSession()
    return dog_name

def get_house_detail(name):
    db = dbda.db('dream_user')
    if (not db.is_table_exist()):      # New a table to insert
        #log.get().info('House not exist, new a table[house]...')
        db.create_house_table()
    temp = db.query_house_by_name(name)
    if len(temp) != 1:
        #log.get().info('House get exception: %s'%(name))
        db.closeSession()
        return
    house_detail = db.get_dict_from_obj(temp[0])
    db.closeSession()
    return house_detail

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
    db.closeSession()
    return secret_list

def get_holding(name):
    db = dbda.db('dream_user')
    temp = db.query_house_by_name(name)
    if len(temp) != 1:
        #log.get().info('House get exception: %s'%(name))
        db.closeSession()
        return
    account_dict = db.get_dict_from_obj(temp[0])
    db.closeSession()
    return ast.literal_eval(account_dict['Holding'])

def get_open_order(user, q_type):
    db = dbdo.db('dream_user')
    order_dest = get_user_type('-')
    if (not db.is_table_exist(order_dest)):      # New a table to insert
        #log.get().info('Order not exist, new a table[%s]...'%('order_%s'%(order_dest)))
        db.create_order_table(order_dest)
        db.closeSession()
        return []
    temp_list = db.query_order_opened(order_dest)
    opened_list = [db.get_dict_from_obj(i) for i in temp_list] 
    db.closeSession()
    return opened_list

def get_market_last(target):
    db = dbdd.db('dream_dog')
    ret = db.query_dog_market_last(target)
    market_last = db.get_dict_from_obj(ret)
    db.closeSession()
    return market_last

def get_market_by_range(target, start, end):
    db = dbdd.db('dream_dog')
    ret = db.query_dog_markey_by_daterange(target, start, end)
    df = pd.DataFrame([db.get_dict_from_obj(i) for i in ret])
    
    # Make sure date soted
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')           # 确保 Close 列为数值类型
    db.closeSession()
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
        db.closeSession()
        return 0.0
    sorted_score_list = sorted(score_list)
    remove_min_max_count = int(len(score_list) * 0.1)     # remove 10%(min&max) of sentiment length
    trimmed_score = sorted_score_list[remove_min_max_count:-remove_min_max_count]
    if len(trimmed_score) == 0:
        db.closeSession()
        return 0.0
    #log.get().info(trimmed_score)
    score_avg = sum(trimmed_score) / len(trimmed_score)
    #log.get().info('Score Avg[%s]: %.2f'%(target, score_avg))
    db.closeSession()
    return score_avg

def get_registered_dog():
    db = dbdr.db('dream_dog')
    ret = db.query_param_by_symbol('registered')
    content = json.loads(db.get_dict_from_obj(ret[0]).get('Content'))
    db.closeSession()
    return content

def get_registered_time(dog_id):
    db = dbdr.db('dream_dog')
    ret = db.query_param_by_symbol('registered')
    registered_time = json.loads(db.get_dict_from_obj(ret[0]).get('Content')).get(dog_id)
    db.closeSession()
    return registered_time

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
    flag = db.update_param_by_symbol('registered', symbol_dict)
    db.closeSession()
    return flag, last_time

def del_registered_dog(dog_id):
    db = dbdr.db('dream_dog')
    content_dict = get_registered_dog()
    del content_dict[dog_id]
    symbol_dict = {
        'Symbol': 'registered',
        'Content': json.dumps(content_dict, default=datetime_converter)
    }
    flag = db.update_param_by_symbol('registered', symbol_dict)
    db.closeSession()
    return flag

def get_dog_realtime_min(dog_id, last_min=0):     # last_min == 0 mean all need to be return
    db = dbdr.db('dream_dog')
    if last_min == 0:
        ret = db.query_sharing_by_dog(dog_id)
    elif last_min >= 1:
        ret = db.query_dog_sharing_last_min(dog_id, last_min)
    temp_list = [db.get_dict_from_obj(n) for n in ret]
    result = sorted(temp_list, key=lambda x: x['DogTime'].split('-')[1], reverse=False)
    db.closeSession()
    return result

def get_dog_realtime_cnt(dog_id, last_cnt=0):     # last_cnt == 0 mean all need to be return
    db = dbdr.db('dream_dog')
    if last_cnt == 0:
        ret = db.query_sharing_by_dog(dog_id)
    elif last_cnt >= 1:
        ret = db.query_dog_sharing_last(dog_id, last_cnt)
    temp_list = [db.get_dict_from_obj(n) for n in ret]
    result = sorted(temp_list, key=lambda x: x['DogTime'].split('-')[1], reverse=False)
    db.closeSession()
    return result

def del_dog_realtime(dog_id):     # last_min == -1 mean all need to be return
    db = dbdr.db('dream_dog')
    if db.is_dog_exist(dog_id):
        db.closeSession()
        return db.del_sharing_by_dogtime(dog_id)
    db.closeSession()
    return True

def get_last_price_from_db(dog_id):
    rt_last_list = get_dog_realtime_cnt(dog_id, 1)
    if len(rt_last_list) > 0:
        rt_last = rt_last_list[-1]
        return float(rt_last.get('Price', 0.00001))
    daily_last = get_market_last(dog_id)
    return float(daily_last.get('Close', 0.00001))

def get_dog_options(dog_id, direction):
    db = create_if_option_inexist()
    ret = db.query_option_by_dog(dog_id, direction)    
    result = [db.get_dict_from_obj(n) for n in ret]
    db.closeSession()
    return result

def update_expectation(market, tmp_dict):
    today_date = datetime.date.today()
    expectation_dict = {'Date':today_date}
    tmp = {'cn':'Cn_Expectation', 'us':'Us_Expectation'}
    expectation_dict.update({tmp.get(market, 'us'):str(tmp_dict)})
    db = dbde.db('dream_dog')
    flag = db.update_expectation_by_date(today_date, expectation_dict)
    db.closeSession()
    return flag

def get_last_expectation(market, today=False):  # If need today's exception, then True
    today_date = datetime.date.today()
    tmp = {'cn':'Cn_Expectation', 'us':'Us_Expectation'}
    db = dbde.db('dream_dog')
    for i in range(10):
        expectation_obj = db.get_latest_expectation(i)
        if expectation_obj == None:
            db.closeSession()
            return {}
        expectation_dict = db.get_dict_from_obj(expectation_obj)
        date_tmp = expectation_dict['Date']
        result_dict_str = expectation_dict.get(tmp.get(market, 'us'), '{}')
        result_dict = ast.literal_eval(result_dict_str)
        if len(result_dict) != 0:
            db.closeSession()
            if (today and date_tmp == datetime.date.today()) or (not today):
                return result_dict
            else:
                return {}
    return {}

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='debug', console_enable=True)
    log.get().info('Logger Creat Success...[%s]'%(py_name))

    start_time = time.time()
    test = get_dog_realtime_min('NVDA', 1000)
    log.get().debug('ElapsedTime get_dog_realtime: %.3f'%(time.time() - start_time))
    log.get().info(test[-2:])


if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)



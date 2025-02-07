#!/bin/python3

# System lib
import os
import sys
import argparse
import datetime
import pandas as pd

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../common'%(py_dir))
from other import is_dog_option
from config import get_global_config
from database import get_market_by_range, get_registered_dog, del_registered_dog
from database import get_dog_realtime, del_dog_realtime
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_dream_dog as dbdd
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def sanity_info(table_name):
    return True

def sanity_market(table_name):
    db = dbdd.db('dream_dog')
    dog_id = table_name[table_name.rfind('_')+1:]
    temp_obj = db.query_dog_market_last(dog_id)
    if (temp_obj == None):
        log.get().info('Market Sanity None:[%s]'%(dog_id))
        return False
    temp_dict = db.get_dict_from_obj(temp_obj)
    temp_date = temp_dict['Date']

    today = datetime.date.today()
    some_days_ago = today - datetime.timedelta(days=10)
    if some_days_ago <= temp_date <= today:
        #log.get().info('Market Sanity Success: [%s]'%(dog_id))
        return True
    else:
        log.get().info('Market Sanity Failed:[%s]'%(dog_id))
        #db.dropTable(table_name)
        return False

def sanity_adjustment_market(table_name):
    dog_id = table_name[table_name.rfind('_')+1:]
    end_date = datetime.datetime.today().date()
    start_date = (datetime.datetime.today() - datetime.timedelta(days=20)).date()
    df = get_market_by_range(dog_id, start_date, end_date)
    if (len(df) == 0):
        return False, None
    df['Close_diff_pct'] = df['Close'].pct_change() * 100
    # diff over 50%
    # for example: 1 share, price $100
    # 1 share -> 2 shares (split), stock price should be half as origin. $100 -> $50, then drop 50%
    # 2 shares -> 1 share (combine), stock price should be double. $100 -> $200, then increase 100%
    # So we take 50% as min diff.
    result = df[df['Close_diff_pct'].abs() > 50]
    output = []
    for i in result.index:
        prev_date = pd.to_datetime(df.iloc[i - 1]['Date']).date()
        prev_close = df.iloc[i - 1]['Close']
        curr_close = df.iloc[i]['Close']
        return False, {'date':prev_date, 'pre':prev_close, 'cur':curr_close}
    return True, None

def sanity_realtime_dog():
    registered_list = [n for n in get_registered_dog()]
    now = datetime.datetime.now()
    for index in registered_list:
        temp_list = get_dog_realtime(index)
        for item in temp_list:
            dog_time = item.get('DogTime', 'XXX-19700101123456')
            timestamp = dog_time.split('-')[1]
            timestamp_obj = datetime.datetime.strptime(timestamp, '%Y%m%d%H%M%S')
            if is_dog_option(index):
                expierd_time = timestamp_obj + datetime.timedelta(days=int(get_global_config('realtime_option_expierd')))
            else:
                expierd_time = timestamp_obj + datetime.timedelta(days=int(get_global_config('realtime_dog_expierd')))
            if now > expierd_time:
                log.get().info('[%s] Expierd, remove from realtime list'%(dog_time))
                del_dog_realtime(dog_time)
    return True

def sanity_realtime_param():
    temp_dict = get_registered_dog()
    now = datetime.datetime.now()
    for dog_id in temp_dict:
        timestamp = temp_dict[dog_id].get('time', '')
        timestamp_obj = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
        if is_dog_option(dog_id):
            expierd_time = timestamp_obj + datetime.timedelta(days=int(get_global_config('realtime_option_expierd')))
        else:
            expierd_time = timestamp_obj + datetime.timedelta(days=int(get_global_config('realtime_dog_expierd')))
        if now > expierd_time:      # Clear all data
            log.get().info('[%s] Expierd, remove all from register list'%(dog_id))
            del_registered_dog(dog_id)
            temp_list = get_dog_realtime(dog_id)
            for item in temp_list:
                del_dog_realtime(item.get('DogTime', 'XXX-19700101123456'))
    return True

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success...')
    bark_obj = notify.bark()

    fail_list = []
    adjusted_dict = {}

    db = dbdd.db('dream_dog')
    table_list = db.queryTable()
    for index in table_list:
        if index.find('info') > 0:
            flag = sanity_info(index)
        elif index.find('market') > 0:
            flag = sanity_market(index)
            if (not flag):
                fail_list.append(index)
            flag, adjust_detail = sanity_adjustment_market(index)
            if (not flag):
                adjusted_dict.update({index:adjust_detail})

    flag = sanity_realtime_param()
    flag = sanity_realtime_dog()

    if len(fail_list) != 0:
        log.get().info('Failed list: %s'%(fail_list))
        flag = bark_obj.send_title_content('Market Sanity', 'Failed list: %s'%(fail_list))
    elif len(adjusted_dict) != 0:
        content = ''
        for adjust_index in adjusted_dict:
            dog_id = adjust_index
            adjust_detail = adjusted_dict[adjust_index]
            if adjust_detail == None:
                log.get().info('Market Adjustment Sanity None:[%s]'%(dog_id))
                content += 'Market Adjustment Sanity None:[%s]\n'%(dog_id)
            else:
                prev_date = adjust_detail['date']
                prev_close = adjust_detail['pre']
                curr_close = adjust_detail['cur']
                log.get().info('[%s] Adjusted in %s [%.2f->%.2f]'%(dog_id, prev_date, prev_close, curr_close))
                content += '[%s] Adjusted in %s [%.2f->%.2f]\n'%(dog_id, prev_date, prev_close, curr_close)
        flag = bark_obj.send_title_content('Market Sanity', '%s'%(content))
    else:
        log.get().info('All market DB works normal')
        #flag = bark_obj.send_title_content('Market Sanity', 'All market DB works normal')
    log.get().info('Bark Notification Result[%s]'%(str(flag)))

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")
    
    # Append arguments
    #parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')
    #parser.add_argument('--quantitative', type=str, default='simulation', help='Now supported: "simulation"(default),"formal"')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)


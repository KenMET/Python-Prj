#!/bin/python3

# System lib
import os
import re
import sys
import argparse
import datetime
import pandas as pd

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
from strategy import basic, get_stategy_handle
sys.path.append(r'%s/../common'%(py_dir))
from config import get_house, get_strategy, get_notify_list, get_trade_list
from database import get_holding, get_market_by_range, get_dogname, get_avg_score
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

# Only for temp during simulation trade test
def merge_holding(quent_type, user_name, notify_list):
    house_holding = get_holding('%s-%s'%(quent_type, user_name))
    for index in house_holding:
        dog_code = index.get('Code')
        dog_code = dog_code[:dog_code.rfind('.US')]     # Support US market fornow
        if dog_code not in notify_list:
            if re.search(r'\d{6}', dog_code):   # Search if have number like '250117'
                log.get().info('Detect share option[%s], skip for now'%(dog_code))
            else:
                notify_list.append(dog_code)
    return notify_list

def get_except_notify(dog_code):
    stategy_handle = get_stategy_handle(dog_code)
    if stategy_handle == None:
        log.get().error('stategy_handle Null')
        return
    current_date = datetime.datetime.now().strftime('%Y%m%d')
    start_date = (datetime.datetime.now() - datetime.timedelta(days=(stategy_handle.long * 2))).strftime('%Y%m%d')
    df = get_market_by_range(dog_code, start_date, current_date)
    next_predict = stategy_handle.mean_reversion_expect(df)
    return next_predict


def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success...[%s]'%(py_name))

    notify_dict = {}
    notify_list = get_notify_list(args.market)
    if args.market == 'us':     # Only for temp during simulation trade test
        notify_list = merge_holding('formal', 'Kanos', notify_list)
    for index in notify_list:
        next_predict = get_except_notify(index)
        if len(next_predict) != 0:
            dog_name = get_dogname(args.market, index)
            notify_dict.update({dog_name:next_predict})
            log.get().info('[%s(%s)]: %s'%(dog_name, index, str(next_predict)))

    if len(notify_dict) != 0:
        bark_obj = notify.bark()
        content = ''
        for index in notify_dict:
            avg_score = get_avg_score(index, 3)
            sub_content = '%s: [%.3f (%.2f) %.3f]\n'%(index, notify_dict[index].get('buy',-1), avg_score, notify_dict[index].get('sell',-1))
            content += sub_content
            log.get().info('Ready to send content: %s'%(sub_content))
        bark_obj.send_title_content('Kanos Stock House', content)

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)

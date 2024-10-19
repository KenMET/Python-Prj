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
from config import get_house, get_strategy
from database import get_holding, get_market_by_range
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log


def pridct_next(quent_type, user_name):
    house_name = '%s-%s'%(quent_type, user_name)
    house_holding = get_holding(house_name)
    log.get().info(house_holding)

    notify_dict = {}
    for hold_index in house_holding:
        dog_code = hold_index.get('Code')
        dog_code = dog_code[:dog_code.rfind('.US')]     # Support US market fornow
        if re.search(r'\d{6}', dog_code):   # Search if have number like '250117'
            log.get().info('Detect share option[%s]'%(dog_code))
        else:
            stategy_handle = get_stategy_handle(dog_code)
            if stategy_handle == None:
                log.get().error('stategy_handle Null')
                return
            current_date = datetime.datetime.now().strftime('%Y%m%d')
            start_date = (datetime.datetime.now() - datetime.timedelta(days=(stategy_handle.long * 2))).strftime('%Y%m%d')
            df = get_market_by_range(dog_code, start_date, current_date)
            next_predict = stategy_handle.mean_reversion_expect(df)
            if len(next_predict) != 0:
                notify_dict.update({dog_code:next_predict})
                log.get().info('[%s]: %s'%(dog_code, str(next_predict)))
    if len(notify_dict) != 0:
        bark_obj = notify.bark()
        content = ''
        for index in notify_dict:
            content += '%s: [0,%.3f]&[%.3f,+∞]\n'%(index, notify_dict[index].get('buy',-1), notify_dict[index].get('sell',-1))
        #bark_obj.send_title_content('Kanos Stock House', content)


def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success...[%s]'%(py_name))
    
    quantitative_type = ['simulation', 'formal']
    house_dict = get_house()
    for user_name in house_dict:
        log.get().info('*******************************************************')
        quent_type = house_dict[user_name].get('quent_type', 'simulation')
        if quent_type == 'both':
            for q_type in quantitative_type:
                log.get().info('------------------------------------------')
                pridct_next(q_type, user_name)
        else:
            pridct_next(quent_type, user_name)


if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    #parser.add_argument('--start', type=str, default='', help='Start Date, for example: 20241001')
    #parser.add_argument('--end', type=str, default='', help='End Date, null as today')
    #parser.add_argument('--target', type=str, default='', help='Backtest dog name')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)


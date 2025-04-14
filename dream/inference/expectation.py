#!/bin/python3

# System lib
import os
import re
import sys
import argparse
import datetime

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
from strategy import get_stategy_handle
sys.path.append(r'%s/../common'%(py_dir))
from config import get_notify_list, get_global_config
from database import create_if_expectation_inexist, update_expectation, get_dog_last_price
from database import get_holding, get_market_by_range, get_dogname, get_avg_score
from other import wait_us_market_open, get_user_type
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

# Only for temp during simulation trade test
def merge_holding(quent_type, user_name, notify_list):
    house_holding = get_holding(get_user_type('-'))
    for index in house_holding:
        dog_code = index.get('Code')
        dog_code = dog_code[:dog_code.rfind('.US')]     # Support US market fornow
        if dog_code not in notify_list:
            if re.search(r'\d{6}', dog_code):   # Search if have number like '250117'
                #log.get().info('Detect share option[%s], skip for now'%(dog_code))
                pass
            else:
                notify_list.append(dog_code)
    return notify_list

def get_expect(dog_code):
    stategy_handle = get_stategy_handle(dog_code, 'long')
    if stategy_handle == None:
        #log.get().error('stategy_handle Null')
        return 0.2, 0.2
    current_date = datetime.datetime.now().strftime('%Y%m%d')
    day_limit = 0
    if hasattr(stategy_handle, 'long'):
        day_limit = stategy_handle.long * 5
    elif hasattr(stategy_handle, 'window_size'):
        day_limit = stategy_handle.window_size * 5
    else:
        return 0.2, 0.2
    start_date = (datetime.datetime.now() - datetime.timedelta(days=day_limit)).strftime('%Y%m%d')
    df = get_market_by_range(dog_code, start_date, current_date)
    return stategy_handle.probability(df, dog_id=dog_code)

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success...[%s]'%(py_name))

    expect_dict = {}
    notify_list = get_notify_list(args.market)
    if args.market == 'us':     # Only for temp during simulation trade test
        if not args.test:
            wait_us_market_open(log.get())
        notify_list = merge_holding('formal', 'Kanos', notify_list)

    bark_obj = notify.bark()
    content = ''
    for index in notify_list:
        dog_name = get_dogname(args.market, index)
        trough_prob, peak_prob = get_expect(index)
        avg_score = get_avg_score(index, 3)
        bollinger_limit = float(get_global_config('bollinger_limit'))
        if trough_prob < bollinger_limit and peak_prob < bollinger_limit:
            log.get().debug('%s: Hold due to [%.2f%% , %.2f%%]'%(dog_name, trough_prob, peak_prob))
            continue
        last_price = get_dog_last_price(index)

        sub_content = '%s(%.2f):[%.2f%% (%.3f) %.2f%%]\n'%(dog_name,
            avg_score, trough_prob, last_price, peak_prob)
        content += sub_content
        log.get().info('%s(%.2f):[%.2f%% (%.3f) %.2f%%]'%(dog_name,
            avg_score, trough_prob, last_price, peak_prob))
        expect_dict.update({index:{
            'trough': trough_prob,
            'peak': peak_prob,
            'avg_score': avg_score,
            'last_price': last_price
        }})

    if len(content) != 0:
        bark_obj.send_title_content('Kanos Stock House', content)
        create_if_expectation_inexist().closeSession()
        flag = update_expectation(args.market, expect_dict)
        if not flag:
            log.get().error('Expectation update failed: %s'%(str(expect_dict)))
    else:
        log.get().info('No expectation today, hold...')

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')
    parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)

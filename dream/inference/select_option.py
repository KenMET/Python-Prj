#!/bin/python3

# System lib
import os
import re
import sys
import math
import random
import argparse
import datetime
import pandas as pd

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
import akshare as ak
sys.path.append(r'%s/../common'%(py_dir))
from config import get_trade_list, get_user_config, get_global_config
from longport_api import quantitative_init, get_quote_context, get_option_dict_from_obj, get_last_price_from_longport
from database import create_if_option_inexist, get_last_price_from_db, get_dog_options, get_last_expectation
from other import wait_us_market_open, retry_func
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success...[%s]'%(py_name))

    if not args.test:
        wait_us_market_open(log.get())

    quantitative_init()
    quote_ctx = get_quote_context()

    #dog_list = get_trade_list('us')
    #log.get().info('dog_list: %s'%(str(dog_list)))

    expierd_min_days = 30 * 4
    dog_price_diff = 0.1
    option_price_min = 5.0
    option_price_max = 15.0

    expectation_dict = get_last_expectation('us', today=True)
    log.get().info('expectation_dict :%s'%(str(expectation_dict)))

    create_if_option_inexist().closeSession()
    bark_obj = notify.bark()
    content = ''
    goal_option_dict = {}
    for dog_index in expectation_dict:
        avg_score = float(expectation_dict.get(dog_index, {}).get('avg_score', 0.0))
        trough_prob = float(expectation_dict.get(dog_index, {}).get('trough', -1.0))
        peak_prob = float(expectation_dict.get(dog_index, {}).get('peak', -1.0))
        option_list = []
        bollinger_limit = float(get_global_config('bollinger_limit'))
        if trough_prob > bollinger_limit:
            option_list += get_dog_options(dog_index, 'C')
        if peak_prob > bollinger_limit:
            option_list += get_dog_options(dog_index, 'P')

        dog_last_price = get_last_price_from_db(dog_index)
        log.get().info('[%s] Last price[%.2f]'%(dog_index, dog_last_price))
        for option_index in option_list:
            symbol = option_index['Symbol']
            match = re.search(r'(\d{6})([CP])(\d+)', symbol)
            if not match:
                log.get().error('[%s] option match failed: %s'%(dog_index, str(option_index)))
                continue
            symbol_type = match.group(2)

            # Filter for days range match
            date_str = match.group(1)
            date_obj = datetime.datetime.strptime(date_str, '%y%m%d').date()
            days_remaining = (date_obj - datetime.date.today()).days
            if expierd_min_days > days_remaining:
                continue

            # Filter for StrikePrice range match
            price_origin = int(match.group(3))
            format_price = round(price_origin / (10 ** (math.floor(math.log10(price_origin)) - math.floor(math.log10(dog_last_price)))), 1)
            if (abs(format_price - dog_last_price) / dog_last_price) > dog_price_diff:
                continue

            last_symbol_price = get_last_price_from_longport(quote_ctx, 'Normal', symbol)     # Using api directly, do not register to realtime service
            if option_price_min <= last_symbol_price <= option_price_max:
                goal_option_list = goal_option_dict.get(symbol_type, [])
                goal_option_list.append(option_index)
                goal_option_dict.update({symbol_type:goal_option_list})
                log.get().info('[%s] %d days target price[%.2f] match option price[%.2f]'%(symbol, days_remaining, format_price, last_symbol_price))

        if len(goal_option_dict.get('C', [])) == 0 and len(goal_option_dict.get('P', [])) == 0:
            continue
        for symbol_type in goal_option_dict:
            goal_option_list = goal_option_dict[symbol_type]
            log.get().debug('goal_option_list[%s]:%s'%(dog_index, str(goal_option_list)))
            temp_option_dict = goal_option_list[random.choice(range(0, len(goal_option_list)))]
            symbol = temp_option_dict.get('Symbol')
            strike_price = temp_option_dict.get('StrikePrice')
            option_price = temp_option_dict.get('Price')
            sub_content = '[%s](%.3f) -> %.3f\n'%(symbol, option_price, strike_price)
            content += sub_content
            log.get().info('Ready to send content: %s'%(sub_content.replace('\n', '')))
    if len(content) > 0:
        flag = retry_func(py_name, bark_obj.send_title_content, ('Option-Advise', content,),
            retry_cnt=3, retry_interval=60, comment='Exception in Option-Advise bark')
 
    # "sentiment_score_definition":  (avg_score)
    #   x <= -0.35: Bearish
    #   -0.35 < x <= -0.15: Somewhat-Bearish
    #   -0.15 < x < 0.15: Neutral
    #   0.15 <= x < 0.35: Somewhat_Bullish
    #   x >= 0.35: Bullish
    #if (-0.15 < avg_score < 0.15) and target_option != 'Put' and target_option != 'Call':
    #    log.get().info('[%s] Neutral, and status not specific'%(dog_code))
    #    continue
    #if (avg_score <= -0.15) and target_option != 'Put' and target_option != 'Drop':
    #    log.get().info('[%s] Bearish, but status expect to sell it. (might to be going down)'%(dog_code))
    #    continue
    #if (avg_score >= 0.15) and target_option != 'Call' and target_option != 'Rise':
    #    log.get().info('[%s] Bullish, but status expect to sell it. (might to be going up)'%(dog_code))
    #    continue

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)

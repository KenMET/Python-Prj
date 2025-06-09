#!/bin/python3

# System lib
import os
import re
import sys
import json
import math
import socket
import argparse
import datetime, time
import pytz

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def is_winter_time():
    ny_tz = pytz.timezone('America/New_York')
    ny_time = datetime.datetime.now(ny_tz)
    return (ny_time.dst() == datetime.timedelta(0))

def wait_us_market_open(logger):
    if is_winter_time():
        logger.info('Sleep 1 hour due to winter time...')
        time.sleep(3600)  # Sleep 1 hour for winter time.
    else:
        logger.info('No need to sleep due to summer time...')

def get_trade_session():
    trade_session = {
        'Pre': {'Start':datetime.time(16, 0, 0), 'End':datetime.time(21, 30, 0)},
        'Normal': {'Start':datetime.time(21, 30, 0), 'End':datetime.time(4, 0, 0)},
        'Post': {'Start':datetime.time(4, 0, 0), 'End':datetime.time(8, 0, 0)},
        'Night': {'Start':datetime.time(8, 0, 0), 'End':datetime.time(16, 0, 0)},
    }
    if is_winter_time():
        trade_session.update({'Pre': {'Start':datetime.time(17, 0, 0), 'End':datetime.time(22, 30, 0)}})
        trade_session.update({'Normal': {'Start':datetime.time(22, 30, 0), 'End':datetime.time(5, 0, 0)}})
        trade_session.update({'Post': {'Start':datetime.time(5, 0, 0), 'End':datetime.time(9, 0, 0)}})
        trade_session.update({'Night': {'Start':datetime.time(9, 0, 0), 'End':datetime.time(17, 0, 0)}})
    return trade_session

def get_current_session_and_remaining_time(last_session):
    trade_session = get_trade_session()
    now = datetime.datetime.now()
    #now = datetime.datetime.strptime('2025-01-02 04:52:00', '%Y-%m-%d %H:%M:%S')
    now_time = now.time()
    today = now.date()

    # Get current session
    current_session = None
    for session, times in trade_session.items():
        start, end = times['Start'], times['End']
        if start < end:  # For 04:00 - 21:30
            if start <= now_time < end:
                current_session = session
                break
        else:  # For 21:30 - 04:00
            if now_time >= start or now_time < end:
                current_session = session
                break

    # Get last session end time
    end_time = datetime.datetime.combine(today, trade_session[last_session]['End'])
    if trade_session[last_session]['Start'] > trade_session[last_session]['End']:
        if now_time >= trade_session[last_session]['Start']:  
            end_time += datetime.timedelta(days=1)
    if now >= end_time:
        end_time += datetime.timedelta(days=1)
    remaining_minutes = int((end_time - now).total_seconds() // 60)

    return current_session, remaining_minutes


def get_user_type(mid_char=''):
    if mid_char == '':
        return os.environ['USER_NAME'], os.environ['USER_TYPE']
    else:
        return '%s%s%s'%(os.environ['USER_NAME'], mid_char, os.environ['USER_TYPE'])

def datetime_converter(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()  # 转换为ISO 8601格式的字符串
    raise TypeError("Type not serializable")

def is_dog_option(dog_id):
    pattern = r'^[A-Za-z]+(\d{6})(C|P)(\d+)$'
    return bool(re.match(pattern, dog_id))

def get_socket_path(service_type):
    return "%s/../tmp/%s_socket"%(py_dir, service_type)    # to dream root dir

def get_dict_from_socket(response):
    received_dict = json.loads(response.decode().replace("'", '"'))
    return received_dict

def push_dict_to_socket(service_type, tmp_dict):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(get_socket_path(service_type))
    client.send(str(tmp_dict).encode())
    response = client.recv(1024 * 10)
    recv_dict = get_dict_from_socket(response)
    client.close()
    return recv_dict

def get_next_inject(a, factor=1.0):
    inc = math.floor(a * factor)
    if inc == a:
        inc += 1
    return inc

def get_prev_inject(total, factor=1.0):
    if 0.99 < factor < 1.01:
        return -1

    if (total + 1) & total == 0:
        prev_total = (total - 1) // 2
        inc = prev_total + 1
    else:
        inc = math.floor(total / 2)

    return inc

def retry_func(logname, func, param, retry_cnt=2, retry_interval=10, comment=''):
    while (retry_cnt > 0):
        try:
            return func(*param)
        except Exception as e:
            retry_cnt -= 1
            log.get(logname).error('Exception in %s: %s'%(str(e), comment))
            time.sleep(retry_interval)
    return None

# Append item to dict
# Scense-1
# Origin: my_dict = {'NVDA': [1, 2, 3, 4], 'TSLA': [6]}
# After append with append_dict_list(my_dict, "NVDA", 5)
# Then print (my_dict) ->
#   my_dict = {'NVDA': [1, 2, 3, 4, 5], 'TSLA': [6]}
#
# Scense-2
# Origin: my_dict = {'NVDA': {'peak':[1, 2], 'trough':[3, 4]}, 'TSLA': {'peak':[5, 6], 'trough':[7, 8]}}
# After append with append_dict_list(my_dict, "NVDA", 10, key_sub='peak')
# Then print (my_dict) ->
#   my_dict = {'NVDA': {'peak':[1, 2，10], 'trough':[3, 4]}, 'TSLA': {'peak':[5, 6], 'trough':[7, 8]}}
def append_dict_list(tmp_dict, key_main, val, key_sub=None):
    if key_sub is None:
        if key_main in tmp_dict:
            tmp_dict[key_main].append(val)
        else:
            tmp_dict[key_main] = [val]
    else:
        if key_main not in tmp_dict:
            tmp_dict[key_main] = {}
        sub_dict = tmp_dict[key_main]
        if key_sub not in sub_dict:
            sub_dict[key_sub] = []
        sub_dict[key_sub].append(val)

def clear_dict_list(tmp_dict, key_main, key_sub=None):
    if key_sub is None:
        if key_main in tmp_dict:
            tmp_dict[key_main] = []
    else:
        if key_main in tmp_dict:
            sub_dict = tmp_dict[key_main]
            if key_sub in sub_dict:
                sub_dict[key_sub] = []

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success...[%s]'%(py_name))

    my_dict1 = {"NVDA": [1, 2, 3]}
    append_dict_list(my_dict1, "NVDA", 4)
    append_dict_list(my_dict1, "TSLA", 6)
    log.get().info('my_dict1:%s'%(str(my_dict1)))

    my_dict2 = {'NVDA': {'peak':[1, 2], 'trough':[3, 4]}, 'TSLA': {'peak':[5, 6], 'trough':[7, 8]}}
    append_dict_list(my_dict2, "NVDA", 10, key_sub='peak')
    log.get().info('my_dict2:%s'%(str(my_dict2)))

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A API subset")

    # Append arguments
    parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)

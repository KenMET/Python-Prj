#!/bin/python3

# System lib
import os
import sys
import json
import random
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
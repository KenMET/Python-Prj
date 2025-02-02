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

def wait_us_market_open(logger):
    ny_tz = pytz.timezone('America/New_York')
    ny_time = datetime.datetime.now(ny_tz)

    is_winter_time = ny_time.dst() == datetime.timedelta(0)

    if is_winter_time:
        logger.info('Sleep 1 hour due to winter time...')
        time.sleep(3600)  # Sleep 1 hour for winter time.

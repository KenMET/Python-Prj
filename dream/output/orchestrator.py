#!/bin/python3

# System lib
import os
import sys
import time
import signal
import argparse
import multiprocessing

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
from long_term import long_term_trade_task
from short_term import short_term_trade_task
from order_monitor import order_monitor_task
sys.path.append(r'%s/../common'%(py_dir))
from other import wait_us_market_open, get_user_type
sys.path.append(r'%s/../../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log
log_name = '%s_%s'%(py_name, get_user_type('_'))

def init_worker():
    """Ignore subprocess's Ctrl+C signal"""
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def main(args):
    log.init('%s/../log'%(py_dir), log_name, log_mode='w', log_level='info', console_enable=True)
    log.get(log_name).info('Logger Creat Success...[%s]'%(log_name))

    if not args.test:
        wait_us_market_open(log.get(log_name))

    try:
        PROCESS_LIMIT = 5
        manager = multiprocessing.Manager()
        queue = manager.Queue()
        pool = multiprocessing.Pool(PROCESS_LIMIT, initializer=init_worker)

        pool.apply_async(long_term_trade_task, args=(queue, log_name,))
        time.sleep(10)  # Interval as 10 second avoid conflict
        pool.apply_async(short_term_trade_task, args=(queue, log_name,))
        time.sleep(10)  # Interval as 10 second avoid conflict
        pool.apply_async(order_monitor_task, args=(queue, log_name,))

        pool.close()
        pool.join()

        try:
            content = 'This round normally exited.'
            notify.bark().send_title_content('Orchestrator-%s'%(get_user_type('-')), content)
        except Exception as e:
            log.get(log_name).error('Exception in Orchestrator bark[%s]: %s'%(content, str(e)))

    except KeyboardInterrupt:
        log.get(log_name).info('Received "Ctrl+C" signal, stop process pool')
        pool.terminate()
        pool.join()
    finally:
        log.get(log_name).debug('Clear resources here...')




if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")

    # Append arguments
    parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)


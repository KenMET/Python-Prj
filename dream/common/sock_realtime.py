#!/bin/python3

# System lib
import os
import sys
import time
import socket
import datetime
import argparse
import threading

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
from config import get_global_config
from other import push_dict_to_socket
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def query_dog(dog_id, last_min=int(get_global_config('realtime_interval'))):
    tmp_dict = {
        'cmd':'query_dog_market',
        'dog_id':dog_id,
        'last_min':last_min,
    }
    return push_dict_to_socket('realtime', tmp_dict)

def register_dog(dog_id):
    tmp_dict = {
        'cmd':'register_dog',
        'dog_id':dog_id,
    }
    return push_dict_to_socket('realtime', tmp_dict)


def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success')

    #recv_dict = query_dog('TSLA', 10)
    #log.get().info('query_dog recv: %s'%(str(recv_dict)))

    recv_dict = register_dog('TSLA')
    log.get().info('register_dog recv: %s'%(str(recv_dict)))



if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A dream will comes ture!")
    
    # Append arguments
    #parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

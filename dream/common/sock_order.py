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
from other import push_dict_to_socket, get_user_type
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def ping_order_sock():
    tmp_dict = {
        'cmd':'ping',
    }
    return push_dict_to_socket(get_user_type('_'), tmp_dict)

def submit_order(dog_id, side, price, share):
    if dog_id.find('.US') <= 0:
        dog_id = dog_id + '.US'
    tmp_dict = {
        'cmd':'submit_order',
        'dog_id':dog_id,
        'side':side,
        'price':price,
        'share':share,
    }
    return push_dict_to_socket(get_user_type('_'), tmp_dict)

def query_order(order_id):
    tmp_dict = {
        'cmd':'query_order',
        'order_id':order_id,
    }
    return push_dict_to_socket(get_user_type('_'), tmp_dict)

def cancel_order(order_id):
    tmp_dict = {
        'cmd':'cancel_order',
        'order_id':order_id,
    }
    return push_dict_to_socket(get_user_type('_'), tmp_dict)

def modify_order(order_id, price, share):
    tmp_dict = {
        'cmd':'modify_order',
        'order_id':order_id,
        'price':price,
        'share':share,
    }
    return push_dict_to_socket(get_user_type('_'), tmp_dict)

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success')

    #recv_dict = submit_order('NVDA.US', 'buy', 99.12, 1)
    #log.get().info('recv_dict: %s'%(str(recv_dict)))
    #order_id = recv_dict['OrderID']
    #time.sleep(5)
    #recv_dict = query_order(order_id)
    #log.get().info('recv_dict: %s'%(str(recv_dict)))
    #time.sleep(5)
    #recv_dict = modify_order(order_id, 123.45, 20)
    #log.get().info('recv_dict: %s'%(str(recv_dict)))
    #time.sleep(5)
    #recv_dict = cancel_order(order_id)
    #log.get().info('recv_dict: %s'%(str(recv_dict)))

    recv_dict = ping_order_sock()
    log.get().info('ping recv: %s'%(str(recv_dict)))

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A dream will comes ture!")
    
    # Append arguments
    #parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

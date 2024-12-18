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
from trade_service import get_socket_path, get_dict_from_socket
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def submit_order(user, q_type, dog_id, side, price, share):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(get_socket_path())
    tmp_dict = {
        'cmd':'submit_order',
        'user':user,
        'type':q_type,
        'dog_id':dog_id,
        'side':side,
        'price':price,
        'share':share,
    }
    client.send(str(tmp_dict).encode())
    response = client.recv(1024 * 10)
    recv_dict = get_dict_from_socket(response)
    client.close()
    return recv_dict

def query_order(user, q_type, order_id):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(get_socket_path())
    tmp_dict = {
        'cmd':'query_order',
        'user':user,
        'type':q_type,
        'order_id':order_id,
    }
    client.send(str(tmp_dict).encode())
    response = client.recv(1024 * 10)
    recv_dict = get_dict_from_socket(response)
    client.close()
    return recv_dict

def cancel_order(user, q_type, order_id):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(get_socket_path())
    tmp_dict = {
        'cmd':'cancel_order',
        'user':user,
        'type':q_type,
        'order_id':order_id,
    }
    client.send(str(tmp_dict).encode())
    response = client.recv(1024 * 10)
    recv_dict = get_dict_from_socket(response)
    client.close()
    return recv_dict

def modify_order(user, q_type, order_id, price, share):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(get_socket_path())
    tmp_dict = {
        'cmd':'modify_order',
        'user':user,
        'type':q_type,
        'order_id':order_id,
        'price':price,
        'share':share,
    }
    client.send(str(tmp_dict).encode())
    response = client.recv(1024 * 10)
    recv_dict = get_dict_from_socket(response)
    client.close()
    return recv_dict

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success')

    recv_dict = submit_order('kanos', 'simulation', 'NVDA.US', 'buy', 99.12, 1)
    log.get().info('recv_dict: %s'%(str(recv_dict)))
    order_id = recv_dict['OrderID']
    time.sleep(5)
    recv_dict = query_order('kanos', 'simulation', order_id)
    log.get().info('recv_dict: %s'%(str(recv_dict)))
    time.sleep(5)
    recv_dict = modify_order('kanos', 'simulation', order_id, 123.45, 20)
    log.get().info('recv_dict: %s'%(str(recv_dict)))
    time.sleep(5)
    recv_dict = cancel_order('kanos', 'simulation', order_id)
    log.get().info('recv_dict: %s'%(str(recv_dict)))


if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A dream will comes ture!")
    
    # Append arguments
    #parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

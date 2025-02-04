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
from dream_service import get_socket_path, get_dict_from_socket
from longport_api import quantitative_init, get_quote_context
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def query_dog(dog_id, last_cnt=0):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(get_socket_path())
    tmp_dict = {
        'cmd':'query_dog_market',
        'dog_id':dog_id,
        'last_cnt':last_cnt,
    }
    client.send(str(tmp_dict).encode())
    response = client.recv(1024 * 10)
    recv_dict = get_dict_from_socket(response)
    client.close()
    return recv_dict

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success')

    #recv_dict = query_dog('TSLA', 10)
    #log.get().info('recv_dict: %s'%(str(recv_dict)))

    quantitative_init('simulation', 'kanos')
    ctx = get_quote_context()
    resp = ctx.capital_distribution('NVDA.US')
    log.get().info(resp)


if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A dream will comes ture!")
    
    # Append arguments
    #parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

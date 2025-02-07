#!/bin/python3

# System lib
import os
import sys
import time
import json
import socket
import datetime
import argparse
import threading

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../common'%(py_dir))
from config import get_global_config
from other import get_socket_path, get_dict_from_socket, get_trade_session
from longport_api import quantitative_init, get_quote_context
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log
log_name = 'trade_%s_%s_%s'%(os.environ['USER_NAME'], os.environ['USER_TYPE'], py_name)

def create_trade_server():
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    socket_path = get_socket_path('trade')
    socket_dir = os.path.dirname(socket_path)
    if not os.path.exists(socket_dir):
        os.makedirs(socket_dir)
    if os.path.exists(socket_path):
        os.remove(socket_path)
    server.bind(socket_path)
    return server

def waiting_client(lock, server, max_client=5):
    try:
        server.listen(max_client)
        while True:
            client_socket, client_address = server.accept()
            client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address, lock, ))
            client_handler.start()
    except Exception as e:
        log.get(log_name).error('Exception captured in waiting_client: %s'%(str(e)))

def handle_client(client_socket, client_address, lock):
    try:
        while True:
            data = client_socket.recv(1024 * 10)
            if not data:
                #log.get(log_name).info("Client %s disconnected"%(str(client_address)))
                break
            recv_dict = get_dict_from_socket(data)
            handle_dict(client_socket, lock, recv_dict)
            #client_socket.sendall(data)  # 将收到的数据回传给客户端
        client_socket.close()
    except Exception as e:
        log.get(log_name).error('Exception captured in handle_client: %s'%(str(e)))

def trade_monitor(lock):
    try:
        while(True):
            log.get(log_name).info('Trade monitor, new looping')

            lock.acquire()
            current_time = datetime.datetime.now()
            timestamp_now = current_time.time()
            lock.release()
            duration_time = (datetime.datetime.now() - current_time).total_seconds()
            time.sleep(int(get_global_config('trade_interval')) - duration_time)
    except Exception as e:
        log.get(log_name).error('Exception captured in trade_monitor: %s'%(str(e)))

def handle_dict(client_socket, lock, tmp_dict):
    log.get(log_name).info('Handle: %s'%(str(tmp_dict)))
    cmd = tmp_dict['cmd']
    ack_dict = {'cmd': '%s_ack'%(cmd)}

    lock.acquire()
    if cmd == 'temp1':
        pass
    elif cmd == 'temp2':
        pass
    else:
        ack_dict.update({'ack':'unknow cmd'})
    lock.release()
    client_socket.sendall(str(ack_dict).encode())

def main(args):
    log.init('%s/../log'%(py_dir), log_name, log_mode='w', log_level='info', console_enable=True)
    log.get(log_name).info('Logger[%s] Create Success'%(log_name))

    lock = threading.Lock()

    trade_t = threading.Thread(target=trade_monitor, args=(lock, ))
    trade_t.start()

    server = create_trade_server()
    waiting_client(lock, server)
    trade_t.join()

    log.get(log_name).error('You should not see this log...')

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A dream will comes ture!")

    # Append arguments
    #parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')

    # 解析命令行参数
    args = parser.parse_args()
    try:
        main(args)
    except Exception as e:
        log.get(log_name).error('Exception captured in main: %s'%(str(e)))

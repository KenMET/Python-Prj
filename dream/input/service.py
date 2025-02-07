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
from database import create_if_realtime_inexist, update_registered_time, get_registered_dog
from database import get_dog_realtime
from other import get_socket_path, get_dict_from_socket, get_trade_session
from longport_api import quantitative_init, get_quote_context
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log
log_name = 'realtime_%s'%(py_name)

def create_trade_server():
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    socket_path = get_socket_path('realtime')
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

def market_monitor(lock):
    db = create_if_realtime_inexist()
    try:
        while(True):
            log.get(log_name).info('Market monitor, new looping')
            trade_session = get_trade_session()
            dog_list = [n for n in get_registered_dog()]

            lock.acquire()
            quantitative_init()
            ctx = get_quote_context()
            current_time = datetime.datetime.now()
            timestamp_now = current_time.time()
            log.get(log_name).info('Market monitor, Quote dog from %s'%(str(dog_list)))
            resp = ctx.quote(["%s.US"%(n) for n in dog_list])
            #log.get(log_name).debug(resp)
            for index in resp:
                dog_code = str(index.symbol).split('.')[0]
                if trade_session['Pre']['Start'] <= timestamp_now < trade_session['Pre']['End']:
                    trading_duration = 'Pre'
                    session_obj = index.pre_market_quote
                elif trade_session['Normal']['Start'] <= timestamp_now < trade_session['Normal']['End']:
                    trading_duration = 'Normal'
                    session_obj = index
                elif trade_session['Post']['Start'] <= timestamp_now < trade_session['Post']['End']:
                    trading_duration = 'Post'
                    session_obj = index.post_market_quote
                elif trade_session['Night']['Start'] <= timestamp_now < trade_session['Night']['End']:   # Not support yet...
                    trading_duration = 'Night'
                    continue
                else:
                    log.get(log_name).error('[%s]Datetime error: %s trade_session:%s'%(dog_code, str(timestamp_now), str(trade_session)))
                    break
                timestamp = session_obj.timestamp.strftime('%Y%m%d%H%M%S')
                dog_time = '%s-%s'%(dog_code, timestamp)
                temp_dict = {
                    'DogTime': dog_time,
                    'Price': float(session_obj.last_done),
                    'Close': float(session_obj.prev_close),
                    #'Open': float(session_obj.open),
                    'High': float(session_obj.high),
                    'Low': float(session_obj.low),
                    'Volume': int(session_obj.volume),
                    'Turnover': float(session_obj.turnover),
                }
                if not db.update_sharing_by_dogtime(dog_time, temp_dict):
                    log.get(log_name).error('[%s]Realtime update failed: %s'%(dog_code, str(temp_dict)))
                log.get(log_name).debug('[%s][%s]:%s'%(trading_duration, dog_time, str(temp_dict)))
            lock.release()
            duration_time = (datetime.datetime.now() - current_time).total_seconds()
            time.sleep(int(get_global_config('realtime_interval')) - duration_time)
    except Exception as e:
        log.get(log_name).error('Exception captured in market_monitor: %s'%(str(e)))

def handle_dict(client_socket, lock, tmp_dict):
    log.get(log_name).info('Handle: %s'%(str(tmp_dict)))
    cmd = tmp_dict['cmd']
    ack_dict = {'cmd': '%s_ack'%(cmd)}

    lock.acquire()
    if cmd == 'register_dog':
        dog_id = tmp_dict['dog_id']
        flag, time = update_registered_time(dog_id)
        if flag:
            log.get(log_name).info('[%s] registered at: %s'%(dog_id, str(time)))
        else:
            log.get(log_name).error('[%s] register failed......'%(dog_id))
        ack_dict.update({'ret':str(flag)})
    elif cmd == 'query_dog_market':
        dog_id = tmp_dict['dog_id']
        last_min = tmp_dict['last_min']
        temp_list = get_dog_realtime(dog_id, last_min)
        ack_dict.update({'ret':temp_list})
    else:
        ack_dict.update({'ack':'unknow cmd'})
    lock.release()
    client_socket.sendall(str(ack_dict).encode())

def main(args):
    log.init('%s/../log'%(py_dir), log_name, log_mode='w', log_level='info', console_enable=True)
    log.get(log_name).info('Logger[%s] Create Success'%(log_name))

    lock = threading.Lock()

    market_t = threading.Thread(target=market_monitor, args=(lock, ))
    market_t.start()

    server = create_trade_server()
    waiting_client(lock, server)
    market_t.join()

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

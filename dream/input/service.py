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
from database import get_dog_realtime_min, get_dog_realtime_cnt
from other import get_socket_path, get_dict_from_socket
from other import is_dog_option, is_winter_time, get_current_session
from longport_api import quantitative_init, quote
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
    db = None
    try:
        while(True):
            loop_start_time = datetime.datetime.now()
            log.get(log_name).info('Market monitor, new looping')
            now_seesion = get_current_session()

            try:
                registered_list = [n for n in get_registered_dog()]
            except Exception as e:
                log.get(log_name).error('Exception captured in market_monitor get_registered_dog: %s'%(str(e)))
                registered_list = []
            dog_list, option_list = list(filter(lambda x: not is_dog_option(x), registered_list)), list(filter(is_dog_option, registered_list))

            #lock.acquire()

            log.get(log_name).info('Market monitor, Quote dog&option from %s'%(str(dog_list+option_list)))
            resp = []
            try:
                resp = quote(dog_list, option_list)
            except Exception as e:
                log.get(log_name).error('Exception captured in market_monitor quote: %s'%(str(e)))
            #log.get(log_name).debug(resp)

            for index in resp:
                log.get(log_name).debug('Market monitor, Test: %s'%(str(index)))
                dog_code = str(index.symbol).split('.')[0]
                session_obj = index     # Default to use normal info
                if now_seesion == 'Pre' and hasattr(index, 'pre_market_quote'):
                    session_obj = index.pre_market_quote
                elif now_seesion == 'Post' and hasattr(index, 'post_market_quote'):
                    session_obj = index.post_market_quote
                elif now_seesion == 'Normal':
                    pass
                elif now_seesion == 'Night':
                    break    # Not support yet
                else:
                    log.get(log_name).error('[%s]Datetime error, now_seesion:%s'%(dog_code, str(now_seesion)))
                    break
                timestamp = session_obj.timestamp.strftime('%Y%m%d%H%M%S')
                time_diff = datetime.datetime.now() - datetime.datetime.strptime(timestamp, '%Y%m%d%H%M%S')
                if time_diff > datetime.timedelta(minutes=30) and not is_dog_option(dog_code):
                    # When normal dog's latest timestamp no update in 30 min, may not a trade day, skip
                    log.get(log_name).info('Market monitor, Maybe not a trade day... %s'%(timestamp))
                    now_seesion = 'Untradeable'
                    break
                if is_dog_option(dog_code) and now_seesion != 'Normal':
                    continue    # Option trade in normal seesion only
                dog_time = '%s-%s'%(dog_code, timestamp)
                temp_dict = {
                    'DogTime': dog_time,    # time from api quote, not from local...
                    'Price': float(session_obj.last_done),
                    'Close': float(session_obj.prev_close),
                    #'Open': float(session_obj.open),
                    'High': float(session_obj.high),
                    'Low': float(session_obj.low),
                    'Volume': int(session_obj.volume),
                    'Turnover': float(session_obj.turnover),
                }
                db = create_if_realtime_inexist()
                if not db.update_sharing_by_dogtime(dog_time, temp_dict):
                    log.get(log_name).error('[%s]Realtime update failed: %s'%(dog_code, str(temp_dict)))
                db.closeSession()
                log.get(log_name).info('[%s][%s]:%s'%(now_seesion, dog_time, str(temp_dict)))
            
            #lock.release()
            if now_seesion == 'Untradeable' or now_seesion == 'Night':
                now = datetime.datetime.now()
                start_hour = 16 if not is_winter_time() else 17
                today_start = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                if now < today_start:
                    time_left = today_start - now
                else:
                    tomorrow_start = today_start + datetime.timedelta(days=1)
                    time_left = tomorrow_start - now
                time_left_sec = int(time_left.total_seconds()) + 10  # Sleep to after market started 10 second
                log.get(log_name).info('[%s] Start sleep %d seconds till market open...'%(now_seesion, time_left_sec))
                time.sleep(time_left_sec)
            else:
                duration_time = (datetime.datetime.now() - loop_start_time).total_seconds()
                time.sleep(int(get_global_config('realtime_interval')) - duration_time)
    except Exception as e:
        if db != None:
            db.closeSession()
        log.get(log_name).error('Exception captured in market_monitor: %s'%(str(e)))

def handle_dict(client_socket, lock, tmp_dict):
    log.get(log_name).info('Handle: %s'%(str(tmp_dict)))
    cmd = tmp_dict['cmd']
    ack_dict = {'cmd': '%s_ack'%(cmd)}

    #lock.acquire()
    if cmd == 'ping':
        log.get(log_name).debug('Ping detected')
        ack_dict.update({'ack':'Ping[%s]'%(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))})
    elif cmd == 'register_dog':
        dog_id = tmp_dict['dog_id']
        log.get(log_name).info('[%s] starting register'%(dog_id))
        flag, time = update_registered_time(dog_id)
        if flag:
            log.get(log_name).info('[%s] registered at: %s'%(dog_id, str(time)))
        else:
            log.get(log_name).error('[%s] register failed......'%(dog_id))
        ack_dict.update({'ret':str(flag)})
    else:
        ack_dict.update({'ack':'unknow cmd'})
    #lock.release()
    client_socket.sendall(str(ack_dict).encode())

def main(args):
    log.init('%s/../log'%(py_dir), log_name, log_mode='w', log_level='info', console_enable=True)
    log.get(log_name).info('Logger[%s] Create Success'%(log_name))

    quantitative_init()

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

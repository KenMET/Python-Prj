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
from database import create_if_order_inexist, get_open_order
from other import get_socket_path, get_dict_from_socket, get_trade_session, get_user_type
from longport_api import quantitative_init
from longport_api import trade_submit, trade_cancel, trade_query, trade_modify
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log
log_name = 'trade_%s_%s'%(get_user_type('_'), py_name)

def create_trade_server():
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    socket_path = get_socket_path(get_user_type('_'))
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

def order_monitor(lock):
    db = None
    try:
        user, quent_type = get_user_type()
        house_name = get_user_type('-')
        
        while(True):
            loop_start_time = datetime.datetime.now()
            log.get(log_name).info('Order monitor, new looping for [%s]'%(house_name))

            log.get(log_name).debug('Order monitor, Getting open order for: %s'%(house_name))
            opened_order_list = get_open_order(user, quent_type)
            lock.acquire()
            log.get(log_name).debug('Order monitor, Lock acquired, start init: %s'%(house_name))
            for order_index in opened_order_list:
                log.get(log_name).debug('Order monitor, Looping in order index: %s'%(str(order_index)))
                order_id = order_index['OrderID']
                order_status = order_index['Status']
                log.get(log_name).debug('Order monitor, query ID: %s'%(order_id))
                order_dict = trade_query(order_id)
                order_query_status = order_dict.get('Status', '')
                log.get(log_name).debug('Order monitor, order_dict: %s'%(str(order_dict)))
                if order_query_status == '':
                    log.get(log_name).error('Query order status failed: %s'%(str(order_dict)))
                    continue
                if order_status != order_query_status:
                    db = create_if_order_inexist(house_name)
                    flag = db.update_order_by_id(house_name, order_id, order_dict)
                    db.closeSession()
                    if not flag:
                        log.get(log_name).error('Order[%s] update failed')
                        continue
                    log.get(log_name).info('[%s][%s] status[%s]->[%s]'%(house_name, order_id, order_status, order_query_status))
                else:
                    order_datetime = order_dict.get('Date', '')
                    if order_datetime == '':
                        log.get(log_name).error('Query order datetime failed: %s'%(str(order_dict)))
                        continue
                    time_obj = datetime.datetime.strptime(order_datetime, '%Y-%m-%d %H:%M:%S.%f')
                    current_time = datetime.datetime.now()
                    log.get(log_name).info('order_time[%s] current_time[%s]'%(order_datetime, str(current_time)))
                    time_diff = current_time - time_obj
                    submit_price = float(order_index['Price'])

                    # get realtime price, temp here
                    realtime_price = submit_price

                    expier_hour = 8     # default waiting hour
                    if abs(realtime_price - submit_price)/submit_price < 0.01:  # diff less than 1%, then keep wait till expire
                        expier_hour = 16
                    if time_diff > datetime.timedelta(hours=expier_hour):
                        log.get(log_name).info('Order expired, cancel: %s'%(order_id))
                        trade_cancel(order_id)
                        continue
                    log.get(log_name).info('[%s][%s] status[%s] no change in %s'%(house_name, order_id, order_status, str(time_diff)))
            lock.release()
            duration_time = (datetime.datetime.now() - loop_start_time).total_seconds()
            time.sleep(int(get_global_config('order_interval')) - duration_time)
        
    except Exception as e:
        if db != None:
            db.closeSession()
        log.get(log_name).error('Exception captured in order_monitor: %s'%(str(e)))


def handle_dict(client_socket, lock, tmp_dict):
    log.get(log_name).info('Handle: %s'%(str(tmp_dict)))
    cmd = tmp_dict['cmd']
    ack_dict = {'cmd': '%s_ack'%(cmd)}

    order_dest = get_user_type('-')
    #lock.acquire()
    if cmd == 'ping':
        log.get(log_name).debug('Ping detected')
        ack_dict.update({'ack':'Ping[%s]'%(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))})
    elif cmd == 'submit_order':
        dog_id = tmp_dict['dog_id']
        side = tmp_dict['side']
        price = tmp_dict['price']
        share = tmp_dict['share']
        log.get(log_name).debug('trade_submit[%s] start'%(dog_id))
        order_dict = trade_submit(dog_id, side, price, share)
        log.get(log_name).debug('trade_submit (%s,%.2f,%d) %s'%(side, price, share, str(order_dict)))
        ack_dict.update(order_dict)
        db = create_if_order_inexist(order_dest)
        log.get(log_name).info('Insert for: %s'%(str(order_dict)))
        flag = db.insert_order(order_dest, order_dict)
        db.closeSession()
        if not flag:
            log.get(log_name).error('Order Inser Error...[%s] %s'%(order_dest, str(order_dict)))
    elif cmd == 'query_order':
        order_id = tmp_dict['order_id']
        log.get(log_name).debug('trade_query[%s] start'%(order_id))
        order_dict = trade_query(order_id)
        log.get(log_name).debug('trade_query[%s] done %s'%(order_id, str(order_dict)))
        ack_dict.update(order_dict)
    elif cmd == 'cancel_order':
        order_id = tmp_dict['order_id']
        log.get(log_name).debug('trade_cancel[%s] start'%(order_id))
        order_dict = trade_cancel(order_id)
        log.get(log_name).debug('trade_cancel[%s] done %s'%(order_id, str(order_dict)))
        ack_dict.update(order_dict)
    elif cmd == 'modify_order':
        order_id = tmp_dict['order_id']
        price = tmp_dict['price']
        share = tmp_dict['share']
        log.get(log_name).debug('trade_modify[%s] start'%(order_id))
        order_dict = trade_modify(order_id, price, share)
        log.get(log_name).debug('trade_modify[%s] (%.2f,%d) %s'%(order_id, price, share, str(order_dict)))
        ack_dict.update(order_dict)
    else:
        ack_dict.update({'ack':'unknow cmd'})
    #lock.release()
    client_socket.sendall(str(ack_dict).encode())

def main(args):
    log.init('%s/../log'%(py_dir), log_name, log_mode='w', log_level='debug', console_enable=True)
    log.get(log_name).info('Logger[%s] Create Success'%(log_name))

    quantitative_init()

    lock = threading.Lock()

    order_t = threading.Thread(target=order_monitor, args=(lock, ))
    order_t.start()

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

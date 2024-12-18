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
from database import create_if_order_inexist
from database import get_house_detail, get_secret_detail, get_open_order
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log
from longport_api import quantitative_init
from longport_api import trade_submit, trade_cancel, trade_query, trade_modify

def get_socket_path():
    return "/tmp/trade_socket"

def get_dict_from_socket(data):
    received_dict = json.loads(data.decode().replace("'", '"'))
    return received_dict

def create_trade_server():
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    socket_path = get_socket_path()
    if os.path.exists(socket_path):
        os.remove(socket_path)
    server.bind(socket_path)
    return server

def waiting_client(lock, server, max_client=5):
    server.listen(max_client)
    while True:
        client_socket, client_address = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address, lock))
        client_handler.start()

def handle_client(client_socket, client_address, lock):
    while True:
        data = client_socket.recv(1024 * 10)
        if not data:
            #log.get(py_name).info("Client %s disconnected"%(str(client_address)))
            break
        recv_dict = get_dict_from_socket(data)
        handle_dict(client_socket, lock, recv_dict)
        #client_socket.sendall(data)  # 将收到的数据回传给客户端
    client_socket.close()

def order_monitor(lock, inteval):
    secret_list = get_secret_detail()
    while(True):
        for index in secret_list:
            user = index['user']
            quent_type = index['type']
            house_name = '%s-%s'%(quent_type, user)
            db = create_if_order_inexist(house_name)
            opened_order_list = get_open_order(user, quent_type)
            lock.acquire()
            quantitative_init(quent_type, user)
            for order_index in opened_order_list:
                order_id = order_index['OrderID']
                order_status = order_index['Status']
                order_dict = trade_query(order_id)
                order_query_status = order_dict.get('Status', '')
                if order_query_status == '':
                    log.get(py_name).error('Query order status failed: %s'%(str(order_dict)))
                    continue
                if order_status != order_query_status:
                    if not db.update_order_by_id(house_name, order_id, order_dict):
                        log.get(py_name).error('Order[%s] update failed')
                        continue
                    log.get(py_name).info('[%s][%s] status[%s]->[%s]'%(house_name, order_id, order_status, order_query_status))
                else:
                    order_datetime = order_dict.get('Date', '')
                    if order_datetime == '':
                        log.get(py_name).error('Query order datetime failed: %s'%(str(order_dict)))
                        continue
                    time_obj = datetime.datetime.strptime(order_datetime, '%Y-%m-%d %H:%M:%S.%f')
                    current_time = datetime.datetime.now()
                    log.get(py_name).info('order_time[%s] current_time[%s]'%(order_datetime, str(current_time)))
                    time_diff = current_time - time_obj
                    if time_diff > datetime.timedelta(minutes=5):
                        log.get(py_name).info('Order expired, cancel: %s'%(order_id))
                        trade_cancel(order_id)
                        continue
                    log.get(py_name).info('[%s][%s] status[%s] no change in %s'%(house_name, order_id, order_status, str(time_diff)))
            lock.release()
        time.sleep(inteval)

def handle_dict(client_socket, lock, tmp_dict):
    log.get(py_name).info('Handle: %s'%(str(tmp_dict)))
    cmd = tmp_dict['cmd']
    ack_dict = {'cmd': '%s_ack'%(cmd)}

    user = tmp_dict['user']
    q_type = tmp_dict['type']
    lock.acquire()
    quantitative_init(q_type, user)
    if cmd == 'submit_order':
        dog_id = tmp_dict['dog_id']
        side = tmp_dict['side']
        price = tmp_dict['price']
        share = tmp_dict['share']
        order_dict = trade_submit(dog_id, side, price, share)
        ack_dict.update(order_dict)
        order_dest = '%s-%s'%(q_type, user)
        db = create_if_order_inexist(order_dest)
        log.get(py_name).info('Insert for: %s'%(str(order_dict)))
        if not db.insert_order(order_dest, order_dict):
            log.get(py_name).error('Order Inser Error...[%s] %s'%(order_dest, str(order_dict)))
    elif cmd == 'query_order':
        order_id = tmp_dict['order_id']
        order_dict = trade_query(order_id)
        ack_dict.update(order_dict)
    elif cmd == 'cancel_order':
        order_id = tmp_dict['order_id']
        order_dict = trade_cancel(order_id)
        ack_dict.update(order_dict)
    elif cmd == 'modify_order':
        order_id = tmp_dict['order_id']
        price = tmp_dict['price']
        share = tmp_dict['share']
        order_dict = trade_modify(order_id, price, share)
        ack_dict.update(order_dict)
    else:
        ack_dict.update({'ack':'unknow cmd'})
    lock.release()
    client_socket.sendall(str(ack_dict).encode())

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get(py_name).info('Service Create Success')

    lock = threading.Lock()
    monitor_t = threading.Thread(target=order_monitor, args=(lock, 60, ))
    monitor_t.start()

    server = create_trade_server()
    waiting_client(lock, server)
    monitor_t.join()

    log.get(py_name).error('You should not see this log...')

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A dream will comes ture!")

    # Append arguments
    #parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')

    # 解析命令行参数
    args = parser.parse_args()
    main(args)

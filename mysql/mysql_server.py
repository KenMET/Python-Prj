#Create By Ken in 2020-04-14
#Modify Log:
#
#
'''
test json:
{"Cmd": "select", "info": {"Name": "Fund"}}
{"Cmd": "show", "info": {"Table": "Head_Table","KeyDict":{"代号":"161725"}}}
'''
import sys
import time
import json
import datetime
import threading
import logging

py_dir = '/home/ken/Code/Python-Prj'
py_name = 'mysql_server'
sys.path.append(r'%s/tcp/'%(py_dir))
sys.path.append(r'%s/mysql/'%(py_dir))
sys.path.append(r'%s/common/alphabet/'%(py_dir))
import tcp
import mysql_lib as ml
import alphabet_pro as alphabet


def mysql_show(mydb, dict_info):
    tmp_dict = {'Table':None, "KeyDict":None}
    for key in tmp_dict:
        tmp = dict_info.get(key, None)
        tmp_dict[key] = tmp
    table_name = tmp_dict['Table']
    key_dict = tmp_dict.get('KeyDict', None)
    return mydb.show_tb(table_name, key_dict)

def mysql_update(mydb, dict_info):
    print (dict_info)
    return 0

def mysql_delete(mydb, dict_info):
    print (dict_info)
    return 0

def mysql_create(mydb, dict_info):
    print (dict_info)
    return 0

def mysql_select(mydb, dict_info):
    tmp_dict = {'Name':None}
    for key in tmp_dict:
        tmp = dict_info.get(key, None)
        tmp_dict[key] = tmp
    data_base_name = tmp_dict['Name']
    mydb.select_db(data_base_name)
    return 0

def mysql_heartbeat(mydb, dict_info): 
    mydb.flush()
    return 0

callback_dict = {
    'show':mysql_show,
    'update':mysql_update,
    'delete':mysql_delete,
    'create':mysql_create,
    'select':mysql_select,
    'heartbeat':mysql_heartbeat,
}

def mysql_recv_process(client, recv_data, mydb):
    recv_str = alphabet.hexbytes2str(recv_data)
    recv_json = json.loads(recv_str)
    logger.info('Recv JSON:%s'%(str(recv_json)))
    cmd = recv_json.get('Cmd', None)
    res_dict = {'Result':None}
    if (cmd == None):
        res_dict['Result'] = 'cmd empty'
        logger.info('Recv Empty CMD of JSON')
        client.send(alphabet.str2hexbytes(json.dumps(res_dict)))
        return
    
    mysql_cb = callback_dict.get(cmd, None)
    if mysql_cb == None:
        res_dict['Result'] = 'cmd error'
        client.send(alphabet.str2hexbytes(json.dumps(res_dict)))
        return
    res = mysql_cb(mydb, recv_json.get('Info', None))
    logger.info('Excute CallBack Function Success')
    res_dict['Result'] = res
    logger.info('Send JSON:%s'%(str(res_dict)))
    client.send(alphabet.str2hexbytes(json.dumps(res_dict, ensure_ascii=False)))

if __name__ == '__main__':
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_name = py_dir + '/mysql/' + py_name + '.log'
    fh = logging.FileHandler(log_name, mode='w')
    fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('Logger Creat Success')
    
    mydb = ml.mysql_client(host="182.61.47.202",user="root")
    server = tcp.tcp_server(1, 'TCP Server', '127.0.0.1', 30001, 4096, 5, mysql_recv_process, (mydb, ))
    logger.info('TCP Server(MySQL) Create Success, Starting Thread')
    server.start()
    server.join()
    mydb.close()
    logger.info('TCP Server(MySQL)[Loger:%s] have an err and exited'%(py_name))
    exit()

#Create By Ken in 2020-04-14
#Modify Log:
#
#
'''
test json:
{"Cmd": "select", "info": {"Name": "Fund"}}
{"Cmd": "show", "info": {"Table": "Head_Table","KeyDict":{"代号":"161725"}}}
'''
import os
import sys
import time
import json
import datetime
import threading
import logging

py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../tcp/'%(py_dir))
sys.path.append(r'%s/../common/alphabet/'%(py_dir))
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

def mysql_recv_process(client, recv_data):
    recv_str = alphabet.hexbytes2str(recv_data)
    recv_json = json.loads(recv_str)
    logger.info('Recv JSON:%s'%(str(recv_json)))
    cmd_num = recv_json.get('CmdNum', 0)
    linear_flag = recv_json.get('Linear', True)
    mydb = ml.mysql_client(host="182.61.47.202",user="root")
    res_dict = {'Result':[]}
    if cmd_num > 0:
        cmd_list = recv_json.get('Cmd', None)
        logger.info("Recv cmd_list: %s"%(str(cmd_list)))
        info_list = recv_json.get('Info', None)
        logger.info("Recv info_list: %s"%(str(info_list)))
    else:
        res_dict['Result'].append("Command number under 1")
        logger.info("Command number under 1")

    for cmd_index in cmd_list:
        if (cmd_index == None):
            res_dict['Result'].append('cmd empty')
            if linear_flag == True:
                logger.info('Recv Empty CMD of JSON, Break')
                break
            else:
                logger.info('Recv Empty CMD of JSON, Continue')
                continue

        mysql_cb = callback_dict.get(cmd_index, None)
        if mysql_cb == None:
            res_dict['Result'].append("Can't find callback[%s]"%(cmd_index))
            if linear_flag == True:
                logger.info("Can't find callback[%s], Break"%(cmd_index))
                break
            else:
                logger.info("Can't find callback[%s], Continue"%(cmd_index))
                continue

        if info_list != None:
            res = mysql_cb(mydb, info_list[cmd_list.index(cmd_index)])
        else:
            res = mysql_cb(mydb, None)
        logger.info('Excute CallBack Function Success')

        res_dict['Result'].append(res)
        logger.info('Send JSON:%s'%(str(res_dict)))

    client.send(alphabet.str2hexbytes(json.dumps(res_dict, ensure_ascii=False)))
    if cmd_num > 0:
        mydb.close()



if __name__ == '__main__':

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_name = py_dir + '/' + py_name + '.log'
    fh = logging.FileHandler(log_name, mode='w')
    fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('Logger Creat Success')

    server = tcp.tcp_server(1, 'TCP Server', '127.0.0.1', 30001, 4096, 5, mysql_recv_process, ())
    logger.info('TCP Server(MySQL) Create Success, Starting Thread')
    server.start()
    server.join()
    
    logger.info('TCP Server(MySQL)[Loger:%s] have an err and exited'%(py_name))
    exit()

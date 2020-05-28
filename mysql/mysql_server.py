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
import datetime
import json

sys.path.append(r'../tcp/')
sys.path.append(r'../common/alphabet/')
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

callback_dict = {
    'show':mysql_show,
    'update':mysql_update,
    'delete':mysql_delete,
    'create':mysql_create,
    'select':mysql_select,
}

def mysql_recv_process(client, recv_data, mydb):
    recv_str = alphabet.hexbytes2str(recv_data)
    recv_json = json.loads(recv_str)
    cmd = recv_json.get('Cmd', None)
    res_dict = {'Result':None}
    if (cmd == None):
        res_dict['Result'] = 'cmd empty'
        client.send(alphabet.str2hexbytes(json.dumps(res_dict)))
        return
    
    mysql_cb = callback_dict.get(cmd, None)
    if mysql_cb == None:
        res_dict['Result'] = 'cmd error'
        client.send(alphabet.str2hexbytes(json.dumps(res_dict)))
        return
    res = mysql_cb(mydb, recv_json.get('Info', None))
    res_dict['Result'] = res
    client.send(alphabet.str2hexbytes(json.dumps(res_dict, ensure_ascii=False)))

if __name__ == '__main__':
    mydb = ml.mysql_client(host="182.61.47.202",user="root")
    server = tcp.tcp_server(1, 'TCP Server', '127.0.0.1', 30001, 4096, 5, mysql_recv_process, (mydb, ))
    server.start()
    server.join()
    mydb.close()

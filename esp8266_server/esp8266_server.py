#python3 -create by ken
import os
import sys
import time
import json
import datetime
import threading
import logging
# esp8266 port always start with 1000, then increase 531, so 1531


py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../tcp/'%(py_dir))
sys.path.append(r'%s/../pipe/'%(py_dir))
sys.path.append(r'%s/../common/alphabet/'%(py_dir))
import tcp
import alphabet_pro as alphabet
import pipe_lib as pipe

#{'name':'Relay0', 'socket':1531},
esp8266_global_list = [
    #{'name':'Relay0', 'socket':1531},
]

heart_beat_cnt = 0

def esp8266_client_send(client, send_data):
    client.send(alphabet.str2hexbytes(send_data + '\r'))

def esp8266_server_recv_process(client, recv_data, logger):
    global esp8266_global_dict, heart_beat_cnt
    recv_str = alphabet.hexbytes2str(recv_data)
    recv_str = recv_str.replace("'", '"')
    if len(recv_str) > 8:
        recv_dict = json.loads(recv_str)
        #logger.info('Recv JSON: %s'%(str(recv_dict)))
        name = recv_dict['name']
        if recv_dict['ctrl'] == 'Register':
            find_flag = False
            for list_index in esp8266_global_list:
                list_index.update({'name':name, 'socket': client})
                logger.info ('Update, %s'%(name))
                find_flag = True
            if not find_flag:
                esp8266_global_list.append({'name':name, 'socket': client})
                logger.info ('New, %s'%(name))
        elif recv_dict['ctrl'] == 'HearBeat':
            heart_beat_cnt += 1
            if heart_beat_cnt >= 500:
                heart_beat_cnt = 0
                logger.info ('Heart beat got 500 times, clear')
            pass

def esp8266_server_send_process(client_pipe, recv_data, logger):
    recv_data = recv_data.replace("'", '"')
    if len(recv_data) > 8:
        recv_dict = json.loads(recv_data)
        logger.info('Pipe Recv JSON: %s'%(str(recv_dict)))
        name = recv_dict['name']
        ctrl = recv_dict['ctrl']
        if name == '' or ctrl == '':
            client_pipe.write('Fail')

        find_flag = False
        for list_index in esp8266_global_list:
            if list_index['name'] == name:
                find_flag = True
                client = list_index['socket']
                echo_dict = {
                    'name': name,
                    'ctrl': ctrl,
                }
                esp8266_client_send(client, str(echo_dict))
                logger.info ('send to %s success[%s]'%(name, str(echo_dict)))
        if find_flag:
            client_pipe.write('Success')
        else:
            client_pipe.write('Fail')


def main():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_name = py_dir + '/' + py_name + '.log'
    fh = logging.FileHandler(log_name, mode='a')
    fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('Logger Creat Success')
    
    esp8266_pipe = pipe.named_pipe('esp8266_ctrl', esp8266_server_send_process, (logger, ))
    esp8266_pipe.create()
    esp8266_pipe.start()
    logger.info ('esp8266_ctrl Pipe create success')
    
    server = tcp.tcp_server(1, 'ESP8266 Server', '192.168.10.16', 1531, 4096, 10, esp8266_server_recv_process, (logger, ))
    server.start()
    logger.info ('ESP8266 Server create success')
    logger.info ('ESP8266 Server running......')
    
    esp8266_pipe.join()
    server.join()

    exit()


if __name__ == '__main__':
    main()
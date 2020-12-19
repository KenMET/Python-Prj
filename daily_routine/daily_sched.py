#Create By Ken in 2020-03-17
#Modify Log:
#
#
import os
import sys
import time
import datetime
import threading
import multiprocessing
import json
from socket import *
import logging
mutex=threading.Lock()

py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../mysql/'%(py_dir))
sys.path.append(r'%s/../spider/'%(py_dir))
sys.path.append(r'%s/../common/alphabet/'%(py_dir))
import mysql_lib as ml
#import logken as log
import spider_fund as spiderF
import alphabet_pro as alphabet

def printTime(logger):
    logger.info(time.strftime('%Y-%m-%d %H:%M:%S'))
    timer_sched(printTime, argv = (logger, ))

def tcp_connect():
    while True:
        try:
            tcpCliSock = socket(AF_INET, SOCK_STREAM)    # open socket
            tcpCliSock.connect(('127.0.0.1', 30001))               # connect to server
            logger.info('Connected MySQL Server')
            return tcpCliSock
        except:
            logger.info('Connecting MySQL Server Fail, Retry in 10s...')
            time.sleep(10)

def heartbeat(logger):
    tcp_client = tcp_connect()
    mysql_cmd = { 'CmdNum': 1, 'Linear': True,
                    'Cmd':['heartbeat']}
    mutexFlag = mutex.acquire(False)
    if mutexFlag:
        tcp_client.send(alphabet.str2hexbytes(json.dumps(mysql_cmd, ensure_ascii=False)))
        res = tcp_recv(tcp_client, logger)
        if res != None:
            recv_json = json.loads(alphabet.hexbytes2str(res))
            logger.info('Heart Beat Echo Recv %s'%(str(recv_json)))
    else:
        logger.info('Heart Beat mutex acquire Fail, push to next period')
    mutex.release()
    timer_sched(heartbeat, argv = (logger, ))
    tcp_client.close()
    

def get_fund_base_info(logger):
    tcp_client = tcp_connect()
    logger.info('get_fund_base_info Enter')
    mysql_cmd = { 'CmdNum': 2, 'Linear': True,
                    'Cmd':['select', 'show'], 
                    'Info':[{'Name':'Fund'}, {'Table':'InfoSummary'}] }

    logger.info('Waiting Muxtex...')
    mutexFlag = mutex.acquire(True)
    logger.info('TCP Send %s'%(str(mysql_cmd)))
    tcp_client.send(alphabet.str2hexbytes(json.dumps(mysql_cmd, ensure_ascii=False)))
    res = tcp_recv(tcp_client, logger)
    if res != None:
        recv_json = json.loads(alphabet.hexbytes2str(res))
        logger.info('TCP Recv %s'%(str(recv_json)))
    logger.info('Muxtex Release...')
    mutex.release()
    code_list = []
    if res != None:
        recv_json = json.loads(alphabet.hexbytes2str(res))
        logger.info('TCP Recv %s'%(str(recv_json)))
        res_list = recv_json['Result'][1]
        logger.info(res_list)
        for index_list in res_list:
            name = index_list[0]
            code = index_list[1]
            code_list.append(code)
            logger.info('Name:%s Code:%s'%(name, code))
        for code_index in code_list:
            logger.info('Starting Process By Code:%s'%(code_index))
            pt = multiprocessing.Process(target=spiderF.main_process,args=(code_index, logger))
            pt.start()
    timer_sched(get_fund_base_info, argv = (logger, ))
    tcp_client.close()


def tcp_recv(tcpCliSock, logger):
    cnt = 0
    while True:
        tcpCliSock.setblocking(0)
        try:
            recv_data = tcpCliSock.recv(4096)
            if len(recv_data) > 0:
                return recv_data
            else:
                tcpCliSock.close()
                return None
        except:
            time.sleep(1)
            cnt = cnt + 1
            if cnt >= 10:
                logger.info('No Data,Timeout...')
                return None





function_list = [
    #[0-开始时间，1-结束时间，2-启动周期，3-回调函数]
    #['00:30:00','10:00:00', '00:00:10', printTime],
    ['00:01:00','23:56:00', '00:05:00', heartbeat],
    ['01:00:00','22:00:00', '03:00:00', get_fund_base_info],
]

def timer_sched(func, argv = (), first_call = False):
    list = []
    for index in function_list:
        if func == index[3]:
            list = index
    if len(list) == 0:
        return -1

    current_day = time.strftime('%Y-%m-%d ')
    current_origin = int(time.mktime(time.strptime(current_day + '0:0:0', "%Y-%m-%d %H:%M:%S")))
    current_time = int(time.mktime(time.strptime(current_day + time.strftime('%H:%M:%S'), "%Y-%m-%d %H:%M:%S")))
    start_time = int(time.mktime(time.strptime(current_day + list[0], "%Y-%m-%d %H:%M:%S")))
    end_time = int(time.mktime(time.strptime(current_day + list[1], "%Y-%m-%d %H:%M:%S")))
    period_time = int(time.mktime(time.strptime(current_day + list[2], "%Y-%m-%d %H:%M:%S"))) - current_origin

    if current_time >= start_time and (current_time - period_time) <= end_time:
        if first_call == True:
            #print ('Start Right Now')
            threading.Timer(0, func, argv).start()
        else:
            #print ('1.Start after %d sec'%(period_time))
            threading.Timer(period_time, func, argv).start()
        return 0

    if (current_time - period_time) > end_time:
        next_origin = int(time.mktime(time.strptime(current_day + '23:59:59', "%Y-%m-%d %H:%M:%S"))) + 1
        period_time = (next_origin - current_time) + (start_time - current_origin)
        #print ('2.Start after %d sec'%(period_time))
        threading.Timer(period_time, func, argv).start()
        return 0 

    if current_time < start_time:
        period_time = start_time - current_time
        #print ('3.Start after %d sec'%(period_time))
        threading.Timer(period_time, func, argv).start()
        return 0



if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_name = py_dir + '/' + py_name + '.log'
    fh = logging.FileHandler(log_name, mode='a')
    fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('Logger Creat Success')

    logger.info('Starting heartbeat...')
    timer_sched(heartbeat, argv = (logger, ), first_call = True)
    logger.info('Starting get_fund_base_info...')
    timer_sched(get_fund_base_info, argv = (logger, ), first_call = True)
    while True:
        time.sleep(65535)
    

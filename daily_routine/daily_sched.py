#Create By Ken in 2020-03-17
#Modify Log:
#
#
import os
import sys
import time
import datetime
import threading
import json
from socket import *

sys.path.append(r'../mysql/')
sys.path.append(r'../common/alphabet/')
import mysql_lib as ml
import alphabet_pro as alphabet


def printTime(tcp_client):
    print (time.strftime('%Y-%m-%d %H:%M:%S'))

function_list = [
    #[0-线程对象，1-开始时间，2-结束时间，3-上次启动时间，4-启动周期，5-回调函数]
    [None, '19:20:00','20:27:00', '00:00:00', '00:00:03', printTime],
]

def is_in_specific_time(start, cur, end):
    s_time = datetime.datetime.strptime(str(datetime.datetime.now().date()) + start, '%Y-%m-%d%H:%M:%S')
    e_time =  datetime.datetime.strptime(str(datetime.datetime.now().date()) + end, '%Y-%m-%d%H:%M:%S')
    if cur >= s_time and cur <= e_time:
        return True
    return False

def is_time_ready(last_time, period, cur):
    period_list = period.split(':')
    next_time = datetime.datetime.strptime(str(datetime.datetime.now().date()) + last_time, '%Y-%m-%d%H:%M:%S')
    next_time += datetime.timedelta(seconds=int(period_list[2]), minutes=int(period_list[1]), hours=int(period_list[0]))
    if cur >= next_time:
        return True
    return False

def timer_sched(cur_time, Args):
    for func_index in function_list:
        flag = is_in_specific_time(func_index[1], cur_time, func_index[2])
        #休眠任务到达开始节点，启动周期任务
        if flag == True:
            if func_index[0] == None:
                func_index[0]=threading.Thread(target=func_index[5],args=Args)
                func_index[3] = cur_time.strftime("%H:%M:%S")
                func_index[0].start()
            else:
                if func_index[0].is_alive() == True:
                    continue
                elif is_time_ready(func_index[3], func_index[4], cur_time) == True:
                    func_index[0]=threading.Thread(target=func_index[5],args=Args)
                    func_index[3] = cur_time.strftime("%H:%M:%S")
                    func_index[0].start()

if __name__ == '__main__':
    tcpCliSock = socket(AF_INET, SOCK_STREAM)    # open socket
    tcpCliSock.connect(('127.0.0.1', 30001))               # connect to server
    while True:
        timer_sched(datetime.datetime.now(), (tcpCliSock, ))
        time.sleep(1)
    

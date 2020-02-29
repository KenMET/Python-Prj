
import sys
import time
import signal
import threading
import binascii
import string
import csv
import codecs
from socket import *

ip = '10.85.152.207'
port = 3002
bufsiz = 1024 * 31


ver_len = 10
ip_len = 4
check_cmd = '55 AA 00 01 03 C2 E3'
psam_status = ['无卡','可用','繁忙','未授权','正获取随机数授权','授权中']
switch_status = ['打开','关闭']

def decode_ip(buff):
    return (str(int(buff[0])) + '.' + str(int(buff[1])) + '.' + str(int(buff[2])) + '.' + str(int(buff[3])))

def recv_data_proc(writer, recv_data):
    offset = 0;
    if recv_data[offset : offset + 2] == b'U\xaa' : #55aa
        offset = offset + 6
        arm_ver = recv_data[offset : offset + ver_len - 1].decode()
        offset = offset + ver_len
        
        inside_ip = decode_ip(recv_data[offset : offset + ip_len])
        offset = offset + ip_len
        
        outside_ip = decode_ip(recv_data[offset : offset + ip_len])
        offset = offset + ip_len + 2 #跳过端口查询
        
        outside_ip_mask = decode_ip(recv_data[offset : offset + ip_len])
        offset = offset + ip_len
        
        outside_ip_gateway = decode_ip(recv_data[offset : offset + ip_len])
        offset = offset + ip_len + 1#跳过硬盘使用率
        
        profile = int(recv_data[offset])
        offset = offset + 1
        
        bst_intervl = int(recv_data[offset])
        offset = offset + 1 + 3#跳过分时长度+功率+PCI
        
        ant_num = int(recv_data[offset])
        offset = offset + 1
        
        emnu = [arm_ver, inside_ip, outside_ip, outside_ip_mask, outside_ip_gateway,
                profile, bst_intervl, ant_num]
        
        for i in range(ant_num):
            ant_ver = recv_data[offset + 1 : offset + ver_len].decode()
            offset = offset + ver_len
            ant_order = int(recv_data[offset])
            offset = offset + 1
            ant_div_order = int(recv_data[offset])
            offset = offset + 1
            ant_power = int(recv_data[offset])
            offset = offset + 1
            ant_switch = switch_status[int(recv_data[offset])]
            offset = offset + 1
            ant_psam1 = psam_status[int(recv_data[offset])]
            offset = offset + 1
            ant_psam2 = psam_status[int(recv_data[offset])]
            offset = offset + 1
            emnu += [ant_ver, ant_order, ant_div_order, ant_power, ant_switch, ant_psam1, ant_psam2]
   
        print (emnu)
        writer.writerow(emnu)


def tcp_send(tcpCliSock, ip_file, cmd):
    while True:
        buff = bytes.fromhex(cmd)
        tcpCliSock.send(buff)
        time.sleep(10)

def tcp_recv(tcpCliSock):
    f_ret = codecs.open("result.csv", "w", 'utf_8_sig')
    writer = csv.writer(f_ret)
    writer.writerow(['ARM版本','内网IP','外网IP','外网子网掩码','外网网关','信道号','BST间隔','天线数量',
                '天线1版本号','天线1车道号','天线1分时次序','天线1功率','天线1开关','天线1PSAM1状态','天线1PSAM2状态',
                '天线2版本号','天线2车道号','天线2分时次序','天线2功率','天线2开关','天线2PSAM1状态','天线2PSAM2状态',
                '天线3版本号','天线3车道号','天线3分时次序','天线3功率','天线3开关','天线3PSAM1状态','天线3PSAM2状态',
                '天线4版本号','天线4车道号','天线4分时次序','天线4功率','天线4开关','天线4PSAM1状态','天线4PSAM2状态',])
    while True:
        recv_data = tcpCliSock.recv(bufsiz)
        recv_data_proc(writer, recv_data)
    f_ret.close()

def main():
    if len(sys.argv) != 2:
        print("arg Err")
        return
    ip_file = sys.argv[1]

    tcpCliSock = socket(AF_INET, SOCK_STREAM)    # open socket
    tcpCliSock.connect((ip, port))               # connect to server

    t2=threading.Thread(target=tcp_recv,args=(tcpCliSock,))
    t2.start()
    time.sleep(1)
    t1=threading.Thread(target=tcp_send,args=(tcpCliSock, ip_file, check_cmd))
    t1.start()




if __name__ == '__main__':
    main()


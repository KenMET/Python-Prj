
import sys
import time
import threading
import copy
from socket import *


sys.path.append(r'../common/alphabet/')
import alphabet_pro

def test_proc(recv_data, a, b):
    print ('recv_data:[%s] args:[%s %d]'%(alphabet_pro.hexbytes2str(recv_data), a, b))


class tcp_server (threading.Thread):
    ClientList = []
    def __init__(self, ThreadID=1, Name='Default', IP='127.0.0.1', Port=531, Bufsiz=4096, ClientLimit=5, CallBack=test_proc, Args=('2',3)):
        threading.Thread.__init__(self)
        self.ThreadID = ThreadID
        self.Name = Name
        self.IP = IP
        self.Port = Port
        self.Bufsiz = Bufsiz
        self.ClientLimit = ClientLimit
        self.CallBack = CallBack
        self.Args = Args
    def run(self):
        print ("开始创建TCP服务器")
        tcp_server = socket(AF_INET, SOCK_STREAM)
        tcp_server.bind((self.IP, self.Port))
        tcp_server.listen(self.ClientLimit)
        while True:
            clientsocket,addr = tcp_server.accept()
            print ('accept connect[%s]'%(str(addr)))
            recv_th=threading.Thread(target=self.tcp_recv,args=(clientsocket, self.Bufsiz))
            recv_th.start()
            client_dict = {'Thread':recv_th, 'Socket':clientsocket, 'IP':addr, }
            self.ClientList.append(client_dict)

    def del_client(self, Thread=None, Socket=None, IP=None):
        for list_index in self.ClientList:
            args_name = ['Thread', 'Socket', 'IP']
            args_tmp = [Thread, Socket, IP]
            for i in range(len(args_name)):
                if list_index[args_name[i]] == args_tmp[i]:
                    print ('Connection Close %s'%(str(list_index['IP'])))
                    list_index['Socket'].close()
                    del self.ClientList[self.ClientList.index(list_index)]
                    return True
        return False    

    def tcp_recv(self, clientsocket, bufsiz):
        recv_data = []
        while True:
            recv_data = clientsocket.recv(bufsiz)
            if not recv_data :
                self.del_client(Socket = clientsocket)
                return False
            self.CallBack(recv_data, *self.Args)
        return True











def tcp_send(Sock, str_tmp):
    print ('TCP Send: %s'%(str_tmp))
    send_bytes = alphabet_pro.hexstr2bytes(str_tmp)
    Sock.send(send_bytes)

def get_single_byte_of_str(str_origin, pos):
    return str_origin[pos*2 : (pos+1)*2]

def get_bytes_of_str(str_origin, pos_start, pos_end):
    if pos_start != 0 or pos_end != 0:
        if pos_start == 0:
            return str_origin[ : pos_end*2]
        else:
            return str_origin[pos_start*2 : ]
    return ''

def get_bcc(inputStr):
    bcc = 0
    for i in (range(len(inputStr)//2)):
        bcc = bcc ^ int(get_single_byte_of_str(inputStr, i), 16)
    return '%s'%(str(bcc))



def c0_send(sock):
    data_temp = '5E6724D0'
    date_time = '20200310132536'
    lane_mode = '03'
    wait_time = '0A'
    tx_power = '03'
    pll_channel_id = '00'
    ef04_opt = '01'
    ef04_read_offset = '0000'
    ef04_read_length = '0000'
    c0_str = '81C0' + data_temp + date_time + lane_mode + wait_time + tx_power
    c0_str += pll_channel_id + ef04_opt + ef04_read_offset + ef04_read_length
    c0_str = 'FFFF' + c0_str.replace('FE','FE00').replace('FF','FE01') + 'FF'
    tcp_send(sock, c0_str)

def c1_send(sock, obuid):
    c1_str = '80C1%s'%(obuid)
    c1_str = c1_str + hex(int(get_bcc(c1_str),10)).replace('0x','').upper()
    c1_str = 'FFFF' + c1_str.replace('FE','FE00').replace('FF','FE01') + 'FF'
    tcp_send(sock, c1_str)

def c2_send(sock, obuid):
    c2_str = '81C2%s01'%(obuid)
    c2_str = c2_str + hex(int(get_bcc(c2_str),10)).replace('0x','').upper()
    c2_str = 'FFFF' + c2_str.replace('FE','FE00').replace('FF','FE01') + 'FF'
    tcp_send(sock, c2_str)

def c6_send(sock, obuid):
    monney = '00000000'
    station_info = '11223344556677889900112233445566778899001122334455667788990011223344556677889900'
    date_time = '20200310121314'

    ef04_offset = '0000'
    ef04_length = '000A'
    ef04_info = '00112233445566778899'

    trade_mode0 = '00' + ef04_offset + ef04_length + ef04_info
    trade_mode1 = '01' + '0000' + '0000'
    trade_mode2 = '02' + ef04_offset + ef04_length + ef04_info
    
    c6_str = '82C6' + obuid + monney + station_info + date_time + trade_mode0
    c6_str = c6_str + hex(int(get_bcc(c6_str),10)).replace('0x','').upper()
    c6_str = 'FFFF' + c6_str.replace('FE','FE00').replace('FF','FE01') + 'FF'
    tcp_send(sock, c6_str)


##############################################################################


def b0_process(sock, info, rsctl):
    if rsctl == '98':
        c0_send(sock)
    else:
        c1_send(sock, '00000000')

def b2_process(sock, info):
    obuid = get_bytes_of_str(info, 0, 4)
    err_code = get_single_byte_of_str(info, 4)
    if err_code == '00':
        c1_send(sock, obuid)
    else:
        c2_send(sock, obuid)

def b3_process(sock, info):
    obuid = get_bytes_of_str(info, 0, 4)
    err_code = get_single_byte_of_str(info, 4)
    if err_code == '00':
        c1_send(sock, obuid)
    else:
        c2_send(sock, obuid)
    
def b4_process(sock, info):
    obuid = get_bytes_of_str(info, 0, 4)
    err_code = get_single_byte_of_str(info, 4)
    if err_code != '00':
        c2_send(sock, obuid)
        return
    card_monney = get_bytes_of_str(info, 5, 9)
    card_0015 = get_bytes_of_str(info, 9, 52)
    card_0019 = get_bytes_of_str(info, 52, 95)
    ef04_read_success_flag = get_bytes_of_str(info, 95, 96)
    ef04_info = get_bytes_of_str(info, 96, 96 + 10)
    c6_send(sock, obuid)

def b5_process(sock, info):
    obuid = get_bytes_of_str(info, 0, 4)
    err_code = get_single_byte_of_str(info, 4)
    if err_code != '00':
        c2_send(sock, obuid)
        return
    c1_send(sock, obuid)



def recv_data_proc(sock, recv_str):
    print ('TCP Recv: %s'%(recv_str))
    rsctl = get_single_byte_of_str(recv_str, 2)
    frame_type = get_single_byte_of_str(recv_str, 3)
    if frame_type == 'B0':
        b0_process(sock, get_bytes_of_str(recv_str, 4, 0), rsctl)
    elif frame_type == 'B2':
        b2_process(sock, get_bytes_of_str(recv_str, 4, 0))
    elif frame_type == 'B3':
        b3_process(sock, get_bytes_of_str(recv_str, 4, 0))
    elif frame_type == 'B4':
        b4_process(sock, get_bytes_of_str(recv_str, 4, 0))
    elif frame_type == 'B5':
        b5_process(sock, get_bytes_of_str(recv_str, 4, 0))

def tcp_recv(tcpCliSock):
    #tcp_send(tcpCliSock, 'C0')
    print ('Tcp Client Wait Data......')
    while True:
        recv_data = tcpCliSock.recv(4096)
        if len(recv_data) > 0:
            recv_data_proc(tcpCliSock, alphabet_pro.bytes2hexstr(recv_data).upper())
        else:
            tcpCliSock.close()
            break

def main():
    tcpCliSock = socket(AF_INET, SOCK_STREAM)    # open socket
    tcpCliSock.connect(('192.168.2.24', 9527))               # connect to server

    t2=threading.Thread(target=tcp_recv,args=(tcpCliSock,))
    t2.start()

if __name__ == '__main__':
    main()

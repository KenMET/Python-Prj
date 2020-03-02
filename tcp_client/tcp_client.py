
import sys
import time
import signal
import threading
import codecs
import copy
from socket import *

recv_callback = 'NULL'
recv_argv = ()
client_list = []

def test_proc(recv_data, a, b, c):
    print ('%s %d %s'%(a, b, c))
    time.sleep(2)

def recv_process_register(cb, argv):
    global recv_callback, recv_argv
    if type(cb) == type(recv_process_register):
        recv_callback = copy.deepcopy(cb)
    else:
        recv_callback = 'NULL'
        return False
    if type(argv) == type((1,2,3)):
        recv_argv = copy.deepcopy(argv)
    else:
        recv_argv = ()
    return True 



def del_client(Thread=None, Socket=None, IP=None):
    global client_list
    for list_index in client_list:
        args_name = ['Thread', 'Socket', 'IP']
        args_tmp = [Thread, Socket, IP]
        for i in range(len(args_name)):
            if list_index[args_name[i]] == args_tmp[i]:
                print ('Connection Close %s'%(str(list_index['IP'])))
                list_index['Socket'].close()
                del client_list[client_list.index(list_index)]
                return True
    return False

def tcp_recv(clientsocket, bufsiz):
    global client_list
    while True:
        recv_data = clientsocket.recv(bufsiz)
        if not recv_data :
            del_client(Socket = clientsocket)
            return False
        if type(recv_callback) == type(tcp_recv):
            recv_callback(recv_data, *recv_argv)
        else:
            print ('recv_callback is str[%s]'%(recv_callback))
    return False

def tcp_accept(tcp_server, bufsiz):
    global client_list
    while True:
        clientsocket,addr = tcp_server.accept()
        print ('accept connect[%s]'%(str(addr)))
        recv_th=threading.Thread(target=tcp_recv,args=(clientsocket, bufsiz))
        recv_th.start()
        client_dict = {'Thread':recv_th, 'Socket':clientsocket, 'IP':addr, }
        client_list.append(client_dict)
        
        

def tcp_start_recv_server(ip, port, bufsiz, listen_num, cb, args_tmp):
    tcp_server = socket(AF_INET, SOCK_STREAM)    # open socket
    tcp_server.bind((ip, port))   #绑定IP和端口
    tcp_server.listen(listen_num)    #监听端口，最多5人排队
    if recv_process_register(cb, args_tmp) == True:
        recv_th=threading.Thread(target=tcp_accept,args=(tcp_server, bufsiz))
        recv_th.start()
    else:
        print ('Err: Start Fail')



def main():
    tcp_start_recv_server('192.168.2.237', 9527, 4096, 5, test_proc, ('12',34,'56'))
    ##

    ##t2=threading.Thread(target=tcp_recv,args=(tcpCliSock,))
    #t2.start()
    #time.sleep(1)
    #t1=threading.Thread(target=tcp_send,args=(tcpCliSock, ip_file, check_cmd))
    #t1.start()




if __name__ == '__main__':
    main()


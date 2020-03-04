
import sys
import time
import signal
import threading
import codecs
import copy
from socket import *



def test_proc(recv_data, a, b):
    print ('%s %d'%(a, b))


class tcp_server (threading.Thread):
    ClientList = []
    def __init__(self, ThreadID=1, Name='Default', IP='127.0.0.1', Port=531, \
                    Bufsiz=4096, ClientLimit=5, CallBack=test_proc, Args=('2',3)):
        threading.Thread.__init__(self)
        self.ThreadID = ThreadID
        self.Name = Name
        self.IP = IP
        self.Port = Port
        self.Bufsiz = Bufsiz
        self.ClientLimit = ClientLimit
        self.CallBack = CallBack
        self.Args = Args
    
def del_client(self, Thread=None, Socket=None, IP=None):
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

    def tcp_recv(self, clientsocket, bufsiz):
        while True:
            recv_data = clientsocket.recv(bufsiz)
            if not recv_data :
                self.del_client(Socket = clientsocket)
                return False
            self.CallBack(recv_data, *recv_argv)
        return True
    
    def tcp_accept(self, tcp_server):
        while True:
            clientsocket,addr = tcp_server.accept()
            print ('accept connect[%s]'%(str(addr)))
            recv_th=threading.Thread(target=self.tcp_recv,args=(clientsocket, self.Bufsiz))
            recv_th.start()
            client_dict = {'Thread':recv_th, 'Socket':clientsocket, 'IP':addr, }
            ClientList.append(client_dict)


    def run(self):
        print ("开始创建TCP服务器")
        tcp_server = socket(AF_INET, SOCK_STREAM)
        tcp_server.bind((self.IP, self.Port))
        tcp_server.listen(self.ClientLimit)
        if recv_process_register(self.CallBack, self.Args) == True:
            recv_th=threading.Thread(target=self.tcp_accept,args=(tcp_server, ))
            recv_th.start()
            return recv_th, tcp_server
        else:
            print ('Err: Start Fail')
        return None, None



def main():
    server = tcp_server(1, 'TCP Server', '192.168.2.237', 9527, 4096, 5, test_proc, ('12', 34, '56',))
    server.start()
    server.join()

if __name__ == '__main__':
    main()


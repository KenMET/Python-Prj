
import sys
import time
import threading
import copy
from socket import *

py_dir = '/home/ken/Code/Python-Prj'
sys.path.append(r'%s/common/alphabet/'%(py_dir))
import alphabet_pro

def test_proc(client, recv_data, a, b):
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
    def run(self):  #Over Write Father Class
        tcp_server = socket(AF_INET, SOCK_STREAM)
        tcp_server.bind((self.IP, self.Port))
        tcp_server.listen(self.ClientLimit)
        print ("TCP Server Generate Successfully")
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
            try:
                recv_data = clientsocket.recv(bufsiz)
                if not recv_data :
                    self.del_client(Socket = clientsocket)
                    return False
                self.CallBack(clientsocket, recv_data, *self.Args)
            except:
                print ('Client Connection Close by peer')
                self.del_client(Socket = clientsocket)
                return False
        return True
    


def main():
    server = tcp_server(1, 'TCP Server', '192.168.189.128', 9527, 4096, 5, test_proc, ('12', 34,))
    server.start()
    server.join()

if __name__ == '__main__':
    main()

#Create By Ken in 2020-03-17
#Modify Log:
#
#
import os
import time
import datetime
import threading
import mysql.connector

def test_proc(recv_data, a, b):
    print ('recv_data:[%s] args:[%s %d]'%(alphabet_pro.hexbytes2str(recv_data), a, b))

class pipe_server (threading.Thread):
    ClientList = []
    def __init__(self, ThreadID=1, Name='Default', Dir='.', Bufsiz=4096, CallBack=test_proc, Args=('2',3)):
        threading.Thread.__init__(self)
        self.ThreadID = ThreadID
        self.Name = Name
        if Dir == '.':
            self.Dir = os.getcwd()
        else:
            self.Dir = Dir
        self.Bufsiz = Bufsiz
        self.CallBack = CallBack
        self.Args = Args
        
    def run(self):  #Over Write Father Class
        try:
            # 创建命名管道
            os.mkfifo(self.Dir + '/%s_in.pipe'%(self.Name))
            os.mkfifo(self.Dir + '/%s_out.pipe'%(self.Name))
        except:
            # 如果命名管道已经创建过了，那么无所谓
            print ("mkfifo error, skip")
        print ("Pipe Server Generate Successfully")
        print ("Pipe[%s] Type is:"%(self.Dir + '/%s_in.pipe'%(self.Name)))
        rf = open(self.Dir + '/%s_in.pipe'%(self.Name), 'r')
        wf = open(self.Dir + '/%s_out.pipe'%(self.Name), 'w')
        print (type(rf))
        while True:
            recv_data = os.read( rf, self.Bufsiz )
            if len(recv_data) == 0:
                continue
            self.CallBack(recv_data, *self.Args)

    def del_pipe(self, Thread=None, Socket=None, IP=None):
        os.close( f )
        os.close( rf )
        return True 














if __name__ == '__main__':
    server = pipe_server(1, 'PipeServer', '.', 4096, test_proc, ('12', 34,))
    server.start()
    server.join()

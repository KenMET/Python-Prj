#python3 -create by ken
import sys
import os, time
import threading


py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]

sys.path.append(r'%s/../common/alphabet/'%(py_dir))
import alphabet_pro as alphabet

echo_str = 'ken_fucking_echo'

def test_proc(client, recv_data, a, b):
    print ('recv_data:[%s] args:[%s %d]'%(alphabet_pro.hexbytes2str(recv_data), a, b))

class named_pipe(threading.Thread):
    def __init__(self, pipe_name='default', pipe_callBack=None, cb_args=('2',3)):
        threading.Thread.__init__(self)
        self.pipe_name = pipe_name
        self.pipe_callBack = pipe_callBack
        self.cb_args = cb_args
        self.write_pipe = None
        self.read_pipe = None
        self.role = 'None'
    def run(self):  #Over Write Father Class
        while True:
            if self.read_pipe == None:
                time.sleep(1)
                continue
            recv_data = self.read(2048)
            if self.pipe_callBack != None:
                self.pipe_callBack(self, recv_data, *self.cb_args)

    def read(self, bufsize):
        read_data = os.read(self.read_pipe, bufsize)
        return alphabet.hexbytes2str(read_data)
        
    def write(self, write_data):
        return os.write(self.write_pipe, alphabet.str2hexbytes(write_data))

    def create(self):
        self.role = 'server'
        write_pipe_file = '/var/tmp/write_pipe_%s'%(self.pipe_name)
        read_pipe_file = '/var/tmp/read_pipe_%s'%(self.pipe_name)
        if os.path.exists(write_pipe_file):
            print ('pipe[%s] exists'%(write_pipe_file))
            os.remove(write_pipe_file)
        if os.path.exists(read_pipe_file):
            print ('pipe[%s] exists'%(read_pipe_file))
            os.remove(read_pipe_file)

        os.mkfifo(read_pipe_file)
        os.mkfifo(write_pipe_file)
        #print ('server start open write_pipe[%s]'%(write_pipe_file))
        self.write_pipe = os.open(write_pipe_file, os.O_SYNC | os.O_CREAT | os.O_RDWR)
        def tmp_echo(write_file, read_file):
            time.sleep(0.1)
            #print ('start echo thread')
            tmp_w_pipe = os.open(write_file, os.O_SYNC | os.O_CREAT | os.O_RDWR)
            os.write(tmp_w_pipe, alphabet.str2hexbytes(echo_str))
            #print ('echo write echo done')
            tmp_r_pipe = os.open(read_file, os.O_RDONLY)
            #print ('echo open read_file done')
            while True:
                buf = alphabet.hexbytes2str(os.read(tmp_r_pipe, 32))
                if buf == echo_str:
                    return 0
                time.sleep(1)

        tmp = threading.Thread(target=tmp_echo, args=(read_pipe_file, write_pipe_file))
        tmp.start()
        #print ('server start open read_pipe[%s]'%(read_pipe_file))
        self.read_pipe = os.open(read_pipe_file, os.O_RDONLY)
        #print ('server open pipe done')
        while True:
            buf = alphabet.hexbytes2str(os.read(self.read_pipe, 32))
            if buf == echo_str:
                self.write(echo_str)
                break
            time.sleep(1)
        tmp.join()
        print ('pipe[%s] create done...'%(self.pipe_name))
        return 0

    def connect(self):
        self.role = 'client'
        #exchange read and write
        write_pipe_file = '/var/tmp/read_pipe_%s'%(self.pipe_name)
        read_pipe_file = '/var/tmp/write_pipe_%s'%(self.pipe_name)
        #print ('client start connect')
        while os.path.exists(write_pipe_file) == False:
            print ('pipe[%s] not exists, waitting......'%(write_pipe_file))
            time.sleep(1)
        self.write_pipe = os.open(write_pipe_file, os.O_SYNC | os.O_CREAT | os.O_RDWR)
        self.read_pipe = os.open(read_pipe_file, os.O_RDONLY)
        print ('pipe[%s] connect done...'%(self.pipe_name))
        return 0



from multiprocessing import Process

def client_cb(client_pipe, recv_data):
    print ('client cb recv:%s'%(recv_data))
    print ('\n')

def test_client_proc():
    cnt = 0
    client_pipe = named_pipe('test', client_cb, ())
    client_pipe.connect()
    client_pipe.start()
    while True:
        cnt = cnt + 1
        print ('client loop send: [%d]'%(cnt))
        client_pipe.write('[%d]'%(cnt))
        time.sleep(5)


def server_cb(server_pipe, recv_data):
    print ('server cb recv: %s'%(recv_data))
    server_pipe.write('server cb echo:%s'%(recv_data))

def test_server_proc():
    server_pipe = named_pipe('test', server_cb, ())
    server_pipe.create()
    server_pipe.start()
    while True:
        time.sleep(60)
    
    
    

def main():
    test_server = Process(target=test_server_proc, args=())
    test_client = Process(target=test_client_proc, args=())
    test_server.start()
    time.sleep(1)
    test_client.start()
    test_client.join()
    test_server.join()
    

if __name__ == '__main__':
    main()

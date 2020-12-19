#python3 -create by ken
import sys
import os, time
import threading

import pipe_lib as pipe

py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]


from multiprocessing import Process

def client_cb(client_pipe, recv_data):
    print ('client1 cb recv:%s'%(recv_data))

def test_client_proc():
    cnt = 0
    client_pipe = pipe.named_pipe('ken_log', client_cb, ())
    client_pipe.connect()
    client_pipe.start()
    print ('client1 connect ok')
    while True:
        cnt = cnt + 1
        print ('client1 loop send: [%d]'%(cnt))
        client_pipe.write('client1:[%d]'%(cnt))
        time.sleep(5)

def client_cb2(client_pipe, recv_data):
    print ('client2 cb recv:%s'%(recv_data))
    print ('\n')

def test_client_proc2():
    cnt = 0
    client_pipe = pipe.named_pipe('ken_log', client_cb2, ())
    client_pipe.connect()
    client_pipe.start()
    print ('client2 connect ok')
    while True:
        cnt = cnt + 1
        print ('client2 loop send: [%d]'%(cnt))
        client_pipe.write('client2:[%d]'%(cnt))
        time.sleep(5)


def main():
    test_client = Process(target=test_client_proc, args=())
    test_client2 = Process(target=test_client_proc2, args=())
    test_client.start()
    test_client2.start()
    test_client.join()
    test_client2.join()


if __name__ == '__main__':
    main()
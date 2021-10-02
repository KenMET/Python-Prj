import sys
import os, time
import threading

from optparse import OptionParser


py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/../pipe/'%(py_dir))
import pipe_lib as pipe

success_flag = False

def esp8266_ctrl_recv_process(client_pipe, recv_data):
    global success_flag
    print('esp8266_ctrl_recv_process recv: %s'%(recv_data))
    if recv_data.find('Success') >= 0:
        success_flag = True


def main(options):
    global success_flag
    if options.dev_name == '' or options.dev_status == '':
        return False

    client_pipe = pipe.named_pipe('esp8266_ctrl', esp8266_ctrl_recv_process, ())
    client_pipe.connect()
    client_pipe.start()
    print ('esp8266_ctrl connect ok')
    success_flag = False
    echo_dict = {'name': options.dev_name, 'ctrl': options.dev_status}
    print (str(echo_dict))
    client_pipe.write(str(echo_dict))
    cnt = 0
    while success_flag == False:
        time.sleep(1)
        cnt = cnt + 1
        if cnt == 10:
            return False
    return True

if __name__ == '__main__':
    usage = "usage: %prog [-n] [-s]" 
    optParser = OptionParser(usage=usage)
    optParser.add_option('-n','--name',type = "string" ,dest = 'dev_name', default = '')
    optParser.add_option('-s','--status',type = "string" ,dest = 'dev_status', default = '')
    (options, args) = optParser.parse_args()
    flag = main(options)
    print ('success_flag: %s'%(str(success_flag)))
    os._exit(0)
    
    

#python3 -create by ken
import sys
import os, time
import threading
import logging
import pipe_lib as pipe

py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]

sys.path.append(r'%s/../common/alphabet/'%(py_dir))
import alphabet_pro as alphabet



def log_cb(log_pipe, recv_data, logger): 
    print('server cb recv: %s'%(recv_data))
    logger.info('server cb recv: %s'%(recv_data))
    #log_pipe.write('server cb echo:%s'%(recv_data))

def main():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_name = py_dir + '/' + py_name + '.log'
    fh = logging.FileHandler(log_name, mode='a')
    fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('Logger Creat Success')

    log_pipe = pipe.named_pipe('ken_log', log_cb, (logger, ))
    log_pipe.create()
    log_pipe.start()
    log_pipe.join()

if __name__ == '__main__':
    main()
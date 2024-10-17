#!/usr/bin/ python3

import os, sys
import logging

py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]

logger_objs = {}
def get(log_name):
    global logger_objs
    log_temp = logger_objs.get(log_name, None)
    if log_temp == None:
        print ('Log not init, using default logger, please init first...')
        if logger_objs.get('default', None) == None:
            print ('Default logger not init yet, start init')
            init(py_dir, 'default')
        return logger_objs.get('default', None)
    return log_temp

def init(py_dir, log_name, log_mode='w', log_level='info', console_enable=True):
    def set_logger(log_name, logger_tmp):
        global logger_objs
        logger_objs.update({log_name:logger_tmp})
    log_file = py_dir + '/' + log_name + '.log'
    logger_tmp = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")

    file_handler = logging.FileHandler(log_file, mode=log_mode)  # 'w':start over writing the file, 'a': Continue writing the file
    file_handler.setFormatter(formatter)

    if (console_enable):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

    if (log_level == 'info'):
        logger_tmp.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        if (console_enable):
            console_handler.setLevel(logging.INFO)
    elif (log_level == 'debug'):
        logger_tmp.setLevel(logging.DEBUG)
        logger_tmp.setLevel(logging.DEBUG)
        if (console_enable):
            console_handler.setLevel(logging.DEBUG)

    logger_tmp.addHandler(file_handler)
    if (console_enable):
        logger_tmp.addHandler(console_handler)
    logger_tmp.info('Logger Creat Success')
    logger_tmp.debug("this is debug") # Enable to modify fh.setLevel(logging.INFO) to logging.DEDBUG
    logger_tmp.warning("this is warning")
    logger_tmp.error("this is error")
    set_logger(log_name, logger_tmp)

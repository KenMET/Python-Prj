# TensorFlow and tf.keras
import tensorflow as tf
print(tf.__version__)

# Helper libraries
import numpy as np
import matplotlib.pyplot as plt
import random

import os, sys
import json
import logging
import tempfile
import optparse
import datetime, time
import threading, multiprocessing, subprocess
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../../../mysql'%(py_dir))
sys.path.append(r'%s/../../../notification'%(py_dir))
sys.path.append(r'%s/../../../common_api/xml_operator'%(py_dir))

import db_dog as cbd
import xml_operator as xo
import notification as notify


logger_g = None
def set_logger(logger):
    global logger_g
    logger_g = logger
def get_logger():
    global logger_g
    return logger_g
def create_logger(file_enable=True, console_enable=True):
    if (not file_enable and not console_enable):
        return None
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_name = py_dir + '/' + py_name + '.log'
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    if (file_enable):
        fh = logging.FileHandler(log_name, mode='w')    # a == append,  w == overwrite
        fh.setLevel(logging.INFO)                       # 输出到file的log等级的开关
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    if (console_enable):
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)                       # 输出到控制台的日志级别开关
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    logger.info('Logger Creat Success')
    #logger.debug("this is debug") # Enable to modify fh.setLevel(logging.INFO) to logging.DEDBUG
    #logger.warning("this is warning")
    #logging.error("this is error")
    return logger

# If you run in a NV docker, please pip install below
# python3 -m pip install sqlalchemy pymysql requests bs4 cryptography mplcursors
# Set env below also
# HOSTNAME=192.168.10.228       PORT=8206
# USERNAME=root                 PASSWORD=XXXXXXXXXXXXXXX
def main():
    db = cbd.dogdb()
    tables = db.queryTable()
    get_logger().info('Dog table count: %d'%(len(tables)))
    if 'dog_lables' not in tables:
        db.create_lable_table()
        get_logger().info('Dog tables created...')
    
    for dog_index in tables:
        if (dog_index.find('dog_money_flow_') < 0):
            continue
        dog_id = dog_index[dog_index.rfind('_')+1:]
        dog_obj_list = db.queryDogLablesById(dog_id)
        if (len(dog_obj_list) == 0):
            get_logger().info('Cannot found dog lables: %s, Start saving the growing'%(dog_id))
            money_flow = db.queryDogMoneyFlowAll(dog_id)
            date_list = []
            value_list = []
            for money_day_grow_index in money_flow:
                dog_money_flow = db.get_dict_from_obj(money_day_grow_index)
                date = dog_money_flow.get('Date')
                date_list.append(date.strftime('%Y-%m-%d'))
                value = dog_money_flow.get('CloseValue')
                value_list.append(float(value))
            x = np.array(date_list)
            y = np.array(value_list)
            fig = plt.figure(figsize=(len(x)//5, 10))
            expected_list = [
                {'Date':'2023-05-31', 'Action':'Buy'},
                {'Date':'2023-06-08', 'Action':'Sell'},
                {'Date':'2023-06-29', 'Action':'Buy'},
                {'Date':'2023-07-03', 'Action':'Sell'},
                {'Date':'2023-07-11', 'Action':'Buy'},
                {'Date':'2023-07-14', 'Action':'Sell'},
                {'Date':'2023-07-24', 'Action':'Buy'},
                {'Date':'2023-07-31', 'Action':'Sell'},
                {'Date':'2023-08-03', 'Action':'Sell'},
                {'Date':'2023-08-24', 'Action':'Buy'},
                {'Date':'2023-08-28', 'Action':'Sell'},
                {'Date':'2023-09-04', 'Action':'Sell'},
            ]
            for index in expected_list:
                x_index = date_list.index(index.get('Date'))
                if (index.get('Action') == 'Buy'):
                    plt.vlines(x=x_index, ymin=0.1, ymax=20, lw=1.5, colors='red', linestyles='--')
                else:
                    plt.vlines(x=x_index, ymin=0.1, ymax=20, lw=1.5, colors='green', linestyles='--')
            plt.plot(x, y)
            plt.xlabel('x - label', fontdict={'color':'red', 'size':10})
            plt.ylabel('y - label', fontdict={'color':'green', 'size':10})
            plt.xticks(size=10, rotation='vertical')
            plt.yticks(size=10)
            fig.savefig('dog.png', facecolor='white')
            dog_db_dict = {'ID':dog_id, 'BestAction':expected_list, 'Reserve':''}
            #flag = db.updateDogLablesByID(dog_id, dog_db_dict)
            #get_logger().info('Dog lables: %s, Insert flag:%s'%(dog_id, str(flag)))
            exit()

if __name__ == '__main__':
    logger = create_logger()
    if ( logger == None ):
        print ('Logger create failed!!!')
        exit()
    set_logger(logger)
    main()

#!/bin/python3

# System lib
import os
import sys
import json
import random
import logging
import hashlib
import datetime, time

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../mysql'%(py_dir))
import db_cat as dbc
import db_dog as dbd
sys.path.append(r'%s/../spider'%(py_dir))
import spider_request as srq
sys.path.append(r'%s/../common_api/xml_operator'%(py_dir))
import xml_operator as xo
import db_cat as dbc

def get_last_quarter():
    date_now = datetime.datetime.now()
    quarter1 = datetime.datetime.strptime('%d-03-31'%(date_now.year), '%Y-%m-%d')
    quarter2 = datetime.datetime.strptime('%d-06-30'%(date_now.year), '%Y-%m-%d')
    quarter3 = datetime.datetime.strptime('%d-09-30'%(date_now.year), '%Y-%m-%d')
    quarter4 = datetime.datetime.strptime('%d-12-31'%(date_now.year), '%Y-%m-%d')
    if date_now < quarter1:
        return '%d-12-31'%(date_now.year-1)
    elif date_now < quarter2:
        return '%d-03-31'%(date_now.year)
    elif date_now < quarter3:
        return '%d-06-30'%(date_now.year)
    elif date_now < quarter4:
        return '%d-09-30'%(date_now.year)

def update(logger):
    file_name = '%s/config.xml'%(py_dir)
    cfg = xo.operator(file_name)
    cfg_dict = cfg.walk_node(cfg.root_node)
    cat_list = cfg_dict.get('cat_list', {}).get('id', [])
    db = dbc.catdb('kanos_cat')
    tables = db.queryTable()

    dog_code_list = []
    for cat_index in cat_list:
        dog_temp_list = db.queryCatHoldingByQuarter(cat_index, get_last_quarter())
        for index in dog_temp_list:
            dog_id = index.DogCodeQuarter[index.DogCodeQuarter.find(':')+1:]
            if (dog_id not in dog_code_list):
                dog_code_list.append(dog_id)
    db.closeSession()

    dog_extra_list = cfg_dict.get('dog_list', {}).get('id', [])
    for dog_extra_index in dog_extra_list:
        if (dog_extra_index not in dog_code_list):
            dog_code_list.append(dog_extra_index)
 
    db = dbd.dogdb('kanos_dog')
    tables = db.queryTable()
    for dog_index in dog_code_list:
        dog_table_name = 'dog_money_flow_%s'%(dog_index)
        if (dog_table_name not in tables):
            db.create_money_flow_table(dog_table_name)
            logger.info('Create table[%s]'%(dog_table_name))
        temp_list = srq.request_dog_money_flows(dog_index)
        logger.info('Table[%s] insert net [%d] row'%(dog_table_name, len(temp_list)))
        for money_flow_index in temp_list:
            #logger.info('Table[%s] update net:%s'%(dog_table_name, str(money_flow_index)))
            flag = db.insertDogMoneyFlow(dog_index, money_flow_index)
            if (not flag):
                date = money_flow_index['Date']
                flag = db.updateDogMoneyFlowByDate(dog_index, date, money_flow_index)
                if (not flag):
                    logger.info ('[Error] - CatNet update failed')
            time.sleep(0.1)

        time.sleep(round(random.uniform(1, 5), 1)) # 1s - 5s, keep 1 float, such as 1.6 and 2.8
    db.closeSession()

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_name = py_dir + '/' + py_name + '.log'
    fh = logging.FileHandler(log_name, mode='a')
    fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('Logger Creat Success')
    #logger.debug("this is debug") # Enable to modify fh.setLevel(logging.INFO) to logging.DEDBUG
    #logger.warning("this is warning")
    #logging.error("this is error")
    update(logger)

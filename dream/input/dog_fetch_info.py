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
import adata
import akshare as ak
import pandas as pd
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_cat as dbc
import db_dream_dog as dbdd
import db_dream_dog_info as dbddi
sys.path.append(r'%s/../../common_api/xml_operator'%(py_dir))
import xml_operator as xo

logger = None
def get_logger():
    global logger
    return logger
def set_logger(logger_tmp):
    global logger
    logger = logger_tmp
def logger_init(log_name=py_name):
    logger_tmp = logging.getLogger()
    logger_tmp.setLevel(logging.INFO)
    log_file = py_dir + '/' + log_name + '.log'
    # file_handler = logging.FileHandler(log_file, mode='a')  # Continue writing the file
    file_handler = logging.FileHandler(log_file, mode='w')  # start over writing the file
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger_tmp.addHandler(file_handler)
    logger_tmp.addHandler(console_handler)
    #logger_tmp.info('Logger Creat Success')
    #logger.debug("this is debug") # Enable to modify fh.setLevel(logging.INFO) to logging.DEDBUG
    #logger.warning("this is warning")
    #logging.error("this is error")
    set_logger(logger_tmp)

def get_config_dict():
    file_name = '%s/config.xml'%(py_dir)
    cfg = xo.operator(file_name)
    cfg_dict = cfg.walk_node(cfg.root_node)
    return cfg_dict

def get_cat_list_from_config():     # From config file(default)
    cfg_dict = get_config_dict()
    cat_list = cfg_dict.get('cat_list', {}).get('id', [])
    if type(cat_list) == type(''):
        cat_list = [cat_list, ]
    return cat_list

def get_cat_list_from_db():         # From cat_survey
    pass

def get_dog_list_from_config():     # From config file(extra_list)
    cfg_dict = get_config_dict()
    dog_list = cfg_dict.get('dog_list', {}).get('id', [])
    if type(dog_list) == type(''):
        dog_list = [dog_list, ]
    return dog_list

def get_dog_list_from_db():         # From cat holding
    def get_last_quarter(offset=0):
        today = datetime.datetime.now().date()
        quarter_ends = [(3, 31), (6, 30), (9, 30), (12, 31)]
        current_quarter = (today.month - 1) // 3 + 1
        target_quarter = (current_quarter + offset - 1) % 4
        target_year = today.year + (current_quarter + offset - 1) // 4
        return datetime.date(target_year, *quarter_ends[target_quarter]).strftime('%Y-%m-%d')

    dog_code_list = []
    cat_list = get_cat_list_from_config()
    db = dbc.catdb('kanos_cat')
    for cat_index in cat_list:
        dog_temp_list = db.queryCatHoldingByQuarter(cat_index, get_last_quarter())
        if len(dog_temp_list) == 0:
            dog_temp_list = db.queryCatHoldingByQuarter(cat_index, get_last_quarter(-1))
            if len(dog_temp_list) == 0:
                dog_temp_list = db.queryCatHoldingByQuarter(cat_index, get_last_quarter(-2))
        for index in dog_temp_list:
            dog_id = index.DogCodeQuarter[index.DogCodeQuarter.find(':')+1:]
            if (dog_id not in dog_code_list):
                dog_code_list.append(dog_id)
    db.closeSession()
    return dog_code_list


def main():
    logger_init()
    get_logger().info('Logger Creat Success')

    df = ak.stock_us_spot_em()
    df = df.dropna(subset=['总市值'])   # Remove Na data
    df.drop(columns=['序号', '涨跌额', '涨跌幅', '开盘价', '最高价', '最低价', '昨收价', '成交量', '成交额', '振幅'], inplace=True)
    df.rename(columns={'名称': 'Name', '最新价': 'Last_Price'}, inplace=True) # Replace title
    df.rename(columns={'总市值': 'Total_Value', '市盈率': 'PE_ratio'}, inplace=True) # Replace title
    df.rename(columns={'换手率': 'Turnover_Rate', '代码': 'Code'}, inplace=True) # Replace title
    df = df.astype(str)
    dog_us_list = df.to_dict(orient='records')

    db = dbddi.db('dream_dog')
    if (not db.is_table_exist()):
        get_logger().info('US dog info table not exist, create...')
        db.create_dog_us_info_table()
    db.delete_dog_us_all()

    for dog_index in dog_us_list:
        flag = db.insert_dog_us(dog_index)
        if (not flag):
            get_logger().info('US dog insert failed: %s'%(str(dog_index)))

if __name__ == '__main__':
    main()

#!/bin/python3

# System lib
import os
import sys
import json
import random
import logging
import hashlib
import argparse
import datetime, time
import pandas as pd
from decimal import Decimal

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
import adata
import akshare as ak
import longport.openapi
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_cat as dbc
import db_dream_dog as dbdd
import db_dream_dog_info as dbddi
import db_dream_secret as dbds
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

def get_dog_list_from_config(market):     # From config file(extra_list)
    cfg_dict = get_config_dict()
    dog_list = cfg_dict.get('dog_%s_list'%(market), {}).get('id', [])
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
        return datetime.date(target_year, *quarter_ends[target_quarter])

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

def get_market(dog_code: str) -> str:
    if dog_code.startswith(('5', '6')):
        return 'sh'
    elif dog_code.startswith(('0', '1', '3')):
        return 'sz'
    elif dog_code.startswith('4'):
        return 'bj'
    else:
        return None

def get_us_fullcode(dod_id):
    db_info = dbddi.db('dream_dog')
    res = db_info.query_dog_fullcode_by_code(args.market, dod_id)
    if len(res) == 0:
        get_logger().error('Dog not found [%s]'%(dod_id))
        return dod_id 
    elif len(res) != 1:
        tmp_list = [i.Code for i in res]
        dog_full_code = [item for item in tmp_list if item.endswith('.' + dod_id)][0]
    else:
        dog_full_code = res[0].Code
    return dog_full_code

# date   open  close   high    low     amount
def get_dog_cn_a_daily_hist(dog_id, **kwargs):
    try:
        df = ak.stock_zh_a_hist(symbol=dog_id, period="daily", adjust="qfq", **kwargs)
        df.drop(columns=['股票代码', '成交量', '振幅', '涨跌幅', '涨跌额', '换手率'], inplace=True)
        df.rename(columns={'日期': 'Date', '开盘': 'Open'}, inplace=True) # Replace title
        df.rename(columns={'收盘': 'Close', '最高': 'High'}, inplace=True) # Replace title
        df.rename(columns={'最低': 'Low', '成交额': 'Amount'}, inplace=True) # Replace title
        return df
    except Exception as e:
        try:
            df = ak.stock_zh_a_daily(symbol=get_market(dog_id)+dog_id, adjust="qfq", **kwargs)
            df.drop(columns=['volume', 'outstanding_share', 'turnover'], inplace=True)
            df.columns = df.columns.str.title()
            return df
        except Exception as e:
            try:
                df = ak.stock_zh_a_hist_tx(symbol=get_market(dog_id)+dog_id, adjust="qfq", **kwargs)
                df.columns = df.columns.str.title()
                df['Amount'] = ((df['Open'] + df['Close'] + df['High'] + df['Low']) / 4) * df['Amount'] * 100
                return df
            except Exception as e:
                get_logger().info('Dog[%s] fetch failed...'%(dog_id))
                return pd.DataFrame()

def get_dog_cn_a_capital_flow(dog_id):
    try:
        df = ak.stock_individual_fund_flow(stock=dog_id, market=get_market(dog_id))
        df.drop(columns=['收盘价', '涨跌幅'], inplace=True)
        df = df.drop(columns=df.filter(like='净占比').columns)
        df.rename(columns={'主力净流入-净额': 'Inflow_Main', '超大单净流入-净额': 'Inflow_Max'}, inplace=True) # Replace title
        df.rename(columns={'大单净流入-净额':'Inflow_Lg', '中单净流入-净额': 'Inflow_Mid'}, inplace=True) # Replace title
        df.rename(columns={'小单净流入-净额': 'Inflow_Sm', '日期': 'Date'}, inplace=True) # Replace title
        return df
    except Exception as e:
        get_logger().info('Dog[%s] capital fetch failed...'%(dog_id))
        return pd.DataFrame()

def get_dog_us_daily_hist(dog_id, **kwargs): 
    try:
        df = ak.stock_us_hist(symbol=dog_id, period="daily", adjust="qfq", **kwargs)
        df.drop(columns=['成交量', '振幅', '涨跌幅', '涨跌额', '换手率'], inplace=True)
        df.rename(columns={'日期': 'Date', '开盘': 'Open'}, inplace=True) # Replace title
        df.rename(columns={'收盘': 'Close', '最高': 'High'}, inplace=True) # Replace title
        df.rename(columns={'最低': 'Low', '成交额': 'Amount'}, inplace=True) # Replace title
        return df
    except Exception as e:
        try:
            get_logger().info('Dog[%s] fetch failed, trying to get from longport...'%(dog_id))
            quote_ctx = longport.openapi.QuoteContext(longport.openapi.Config.from_env())
            if 'start_date' in kwargs and 'end_date' in kwargs:
                start = datetime.datetime.strptime(kwargs['start_date'], '%Y%m%d').date()
                end = datetime.datetime.strptime(kwargs['end_date'], '%Y%m%d').date()
                resp = quote_ctx.history_candlesticks_by_date("%s.US"%(dog_id), longport.openapi.Period.Day,
                    longport.openapi.AdjustType.ForwardAdjust, start = start, end = end)
            else:
                resp = quote_ctx.history_candlesticks_by_date("%s.US"%(dog_id), longport.openapi.Period.Day, 
                    longport.openapi.AdjustType.ForwardAdjust)
            df_list = []
            for index in resp:
                tmp_dict = {
                    'Date':index.timestamp.date(), 'Amount':str(index.turnover),
                    'Open':str(index.open), 'Close':str(index.close),
                    'High':str(index.high),'Low':str(index.low),    
                }
                df_list.append(tmp_dict)
            df = pd.DataFrame(df_list)
            return df
        except Exception as e:
            return pd.DataFrame()

def quantitative_init(quant_type):
    db = dbds.db('dream_sentiment')
    if (not db.is_table_exist()):
        get_logger().info('Quantitative table not exist, new a table...')
        db.create_secret_table()
    res = db.query_secret_by_type(quant_type)
    if len(res) != 1:
        return
    os.environ['LONGPORT_APP_KEY'] = res[0].App_Key
    os.environ['LONGPORT_APP_SECRET'] = res[0].App_Secret
    os.environ['LONGPORT_ACCESS_TOKEN'] = res[0].Access_Token

def main(args):
    logger_init()
    get_logger().info('Logger Creat Success')

    quantitative_init(args.quantitative)

    dog_list = []
    if (args.market == 'us'):
        dog_list = get_dog_list_from_config(args.market)
        get_logger().info(dog_list)
    elif (args.market == 'cn_a'):
        dog_list = get_dog_list_from_db()
        dog_list = list(set(dog_list).union(get_dog_list_from_config(args.market)))

    db = dbdd.db('dream_dog')
    for dog_index in dog_list:
        if (not db.is_table_exist(dog_index)):      # New a table to insert
            get_logger().info('Dog[%s] not exist, new a table...'%(dog_index))
            db.create_dog_market_table(dog_index)
            if (args.market == 'us'):
                dog_full_code = get_us_fullcode(dog_index)
                df = get_dog_us_daily_hist(dog_full_code)
                if (df.empty):  
                    continue 
            elif (args.market == 'cn_a'):
                df1 = get_dog_cn_a_daily_hist(dog_index)
                if (df1.empty):
                    continue
                df2 = get_dog_cn_a_capital_flow(dog_index)
                if (df2.empty):
                    df = df1
                else:
                    df = pd.merge(df1, df2, on='Date', how='left')
                    df.fillna(0, inplace=True)
        else:
            current_date = datetime.datetime.now().strftime('%Y%m%d')
            start_date = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y%m%d')    # 10 days ago
            if (args.market == 'us'):
                dog_full_code = get_us_fullcode(dog_index)
                df = get_dog_us_daily_hist(dog_full_code, start_date=start_date, end_date=current_date)
                if (df.empty):  
                    continue 
            elif (args.market == 'cn_a'):
                df1 = get_dog_cn_a_daily_hist(dog_index, start_date=start_date, end_date=current_date)
                if (df1.empty):
                    continue
                df2 = get_dog_cn_a_capital_flow(dog_index)
                if (df2.empty):
                    df = df1
                else:
                    df = pd.merge(df1, df2, on='Date', how='left')
                    df.fillna(0, inplace=True)
        dog_update_list = df.to_dict(orient='records')
        get_logger().info('Start insert for [%s]'%(dog_index))
        for dog_update_index in dog_update_list:
            #get_logger().info(dog_update_index)
            flag = db.insert_dog_market(dog_index, dog_update_index)
            if (not flag):
                get_logger().info('dog insert failed: %s'%(str(dog_update_index)))

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")
    
    # Append arguments
    parser.add_argument('--market', type=str, default='cn_a', help='Now supported: "cn_a"(default),"us"')
    parser.add_argument('--quantitative', type=str, default='simulation', help='Now supported: "simulation"(default),"formal"')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

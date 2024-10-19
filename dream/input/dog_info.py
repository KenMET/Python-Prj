#!/bin/python3

# System lib
import os, sys
import argparse

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
import akshare as ak
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_dream_dog_info as dbddi
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get(py_name).info('Logger Creat Success')

    if (args.market == 'cn_a'):
        df = ak.stock_zh_a_spot_em()
        df = df.dropna(subset=['总市值'])   # Remove Na data
        df.drop(columns=['序号', '涨跌额', '涨跌幅', '今开', '最高', '最低', '昨收', '成交量', '成交额', '振幅', '量比'], inplace=True)
        df.drop(columns=['年初至今涨跌幅', '60日涨跌幅', '5分钟涨跌', '涨速', '流通市值', '市净率'], inplace=True)
        df.rename(columns={'总市值': 'Total_Value', '市盈率-动态': 'PE_ratio'}, inplace=True) # Replace title
    elif (args.market == 'us'):
        df = ak.stock_us_spot_em()
        df = df.dropna(subset=['总市值'])   # Remove Na data
        df.drop(columns=['序号', '涨跌额', '涨跌幅', '开盘价', '最高价', '最低价', '昨收价', '成交量', '成交额', '振幅'], inplace=True)
        df.rename(columns={'总市值': 'Total_Value', '市盈率': 'PE_ratio'}, inplace=True) # Replace title

    df.rename(columns={'名称': 'Name', '最新价': 'Last_Price'}, inplace=True) # Replace title
    df.rename(columns={'换手率': 'Turnover_Rate', '代码': 'Code'}, inplace=True) # Replace title
    df = df.astype(str)
    dog_list = df.to_dict(orient='records')

    db = dbddi.db('dream_dog')
    if (not db.is_table_exist(args.market)):
        log.get(py_name).info('%s dog info table not exist, create...'%(args.market))
        db.create_dog_info_table(args.market)
    db.delete_dog_all(args.market)

    for dog_index in dog_list:
        flag = db.insert_dog(args.market, dog_index)
        if (not flag):
            log.get(py_name).info('%s dog insert failed: %s'%(args.market, str(dog_index)))

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")
    
    # Append arguments
    parser.add_argument('--market', type=str, default='cn_a', help='Now supported: "cn_a"(default),"us"')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

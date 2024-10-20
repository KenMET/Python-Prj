#!/bin/python3

# System lib
import os
import sys
import argparse
import datetime
import pandas as pd

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
import akshare as ak
sys.path.append(r'%s/../common'%(py_dir))
from config import get_dog
from longport_api import quantitative_init, get_history
from database import get_us_fullcode, create_if_market_inexist
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def get_market(dog_code: str) -> str:
    if dog_code.startswith(('5', '6')):
        return 'sh'
    elif dog_code.startswith(('0', '1', '3')):
        return 'sz'
    elif dog_code.startswith('4'):
        return 'bj'
    else:
        return None

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
        log.get().info('Exception level-1, try opt-2...')
        try:
            df = ak.stock_zh_a_hist_tx(symbol=get_market(dog_id)+dog_id, adjust="qfq", **kwargs)
            df.columns = df.columns.str.title()
            df['Amount'] = ((df['Open'] + df['Close'] + df['High'] + df['Low']) / 4) * df['Amount'] * 100
            return df
        except Exception as e:
            log.get().info('Exception level-2, try opt-3...')
            try:
                df = ak.stock_zh_a_daily(symbol=get_market(dog_id)+dog_id, adjust="qfq", **kwargs)
                df.drop(columns=['volume', 'outstanding_share', 'turnover'], inplace=True)
                df.columns = df.columns.str.title()
                return df
            except Exception as e:
                log.get().info('Dog[%s] fetch failed...'%(dog_id))
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
        log.get().info('Dog[%s] capital fetch failed...'%(dog_id))
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
            log.get().info('Dog[%s] fetch failed, trying to get from longport...'%(dog_id))
            quote_ctx = get_quote_context()
            if 'start_date' in kwargs and 'end_date' in kwargs:
                start = datetime.datetime.strptime(kwargs['start_date'], '%Y%m%d').date()
                end = datetime.datetime.strptime(kwargs['end_date'], '%Y%m%d').date()
                resp = get_history("%s.US"%(dog_id), start=start, end=end)
            else:
                resp = get_history("%s.US"%(dog_id))
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

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success')

    quantitative_init('Kanos', args.quantitative)

    dog_list = []
    if (args.market == 'us'):
        dog_list = get_dog(args.market)
        log.get().info(dog_list)
    elif (args.market == 'cn_a'):
        dog_list = []
        dog_list = list(set(dog_list).union(get_dog(args.market)))

    for dog_index in dog_list:
        db, inexist = create_if_market_inexist(dog_index)
        if inexist:
            if (args.market == 'us'):
                dog_full_code = get_us_fullcode(args.market, dog_index)
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
                dog_full_code = get_us_fullcode(args.market, dog_index)
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
        log.get().info('Start insert for [%s]'%(dog_index))
        for dog_update_index in dog_update_list:
            #log.get().info(dog_update_index)
            flag = db.insert_dog_market(dog_index, dog_update_index)
            if (not flag):
                log.get().info('dog insert failed: %s'%(str(dog_update_index)))

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")
    
    # Append arguments
    parser.add_argument('--market', type=str, default='cn_a', help='Now supported: "cn_a"(default),"us"')
    parser.add_argument('--quantitative', type=str, default='simulation', help='Now supported: "simulation"(default),"formal"')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

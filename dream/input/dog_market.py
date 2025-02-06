#!/bin/python3

# System lib
import os
import sys
import math
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
from longport_api import quantitative_init, get_history, get_quote_context
from database import get_fullcode, create_if_market_inexist
from standard import wait_us_market_open
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def get_market(dog_code: str) -> str:
    if dog_code.startswith(('5', '6')):
        return 'sh'
    elif dog_code.startswith(('0', '1', '3')):
        return 'sz'
    elif dog_code.startswith('4'):
        return 'bj'
    elif len(dog_code)==8 and dog_code[:2].isalpha() and dog_code[2:].isdigit():
        return dog_code[:2]
    else:
        return None

# Filter for CN dog ID
def get_cn_dog_id(dog_code: str) -> str:
    return ''.join([c for c in dog_code if c.isdigit()])

# date   open  close   high    low     amount
def get_dog_cn_daily_hist(dog_id, **kwargs):
    dog_id_filter = get_cn_dog_id(dog_id)
    try:
        df = ak.stock_zh_a_hist(symbol=dog_id, period="daily", adjust="qfq", **kwargs)  # Do not fetch dog such as "sh000016" here, skip to opt-2
        df.drop(columns=['股票代码', '成交量', '振幅', '涨跌幅', '涨跌额', '换手率'], inplace=True)
        df.rename(columns={'日期': 'Date', '开盘': 'Open'}, inplace=True) # Replace title
        df.rename(columns={'收盘': 'Close', '最高': 'High'}, inplace=True) # Replace title
        df.rename(columns={'最低': 'Low', '成交额': 'Amount'}, inplace=True) # Replace title
        return df
    except Exception as e:
        log.get().info('[%s]Exception level-1, try opt-2...', dog_id)
        try:
            df = ak.stock_zh_a_hist_tx(symbol=get_market(dog_id)+dog_id_filter, adjust="qfq", **kwargs)
            df.columns = df.columns.str.title()
            df['Amount'] = ((df['Open'] + df['Close'] + df['High'] + df['Low']) / 4) * df['Amount'] * 100
            return df
        except Exception as e:
            log.get().info('[%s]Exception level-2, try opt-3...', dog_id)
            try:
                df = ak.stock_zh_a_daily(symbol=get_market(dog_id)+dog_id_filter, adjust="qfq", **kwargs)
                df.drop(columns=['volume', 'outstanding_share', 'turnover'], inplace=True)
                df.columns = df.columns.str.title()
                return df
            except Exception as e:
                log.get().error('Dog[%s] fetch failed: %s'%(dog_id, str(e)))
                return pd.DataFrame()

def get_dog_cn_capital_flow(dog_id):
    dog_id_filter = get_cn_dog_id(dog_id)
    try:
        df = ak.stock_individual_fund_flow(stock=dog_id_filter, market=get_market(dog_id))
        df.drop(columns=['收盘价', '涨跌幅'], inplace=True)
        df = df.drop(columns=df.filter(like='净占比').columns)
        df.rename(columns={'主力净流入-净额': 'Inflow_Main', '超大单净流入-净额': 'Inflow_Max'}, inplace=True) # Replace title
        df.rename(columns={'大单净流入-净额':'Inflow_Lg', '中单净流入-净额': 'Inflow_Mid'}, inplace=True) # Replace title
        df.rename(columns={'小单净流入-净额': 'Inflow_Sm', '日期': 'Date'}, inplace=True) # Replace title
        return df
    except Exception as e:
        log.get().error('Dog[%s] capital fetch failed...'%(dog_id))
        return pd.DataFrame()

def get_dog_us_daily_hist(dog_id, **kwargs): 
    try:
        df = ak.stock_us_hist(symbol=dog_id, period="daily", adjust="qfq", **kwargs)
        df.drop(columns=['成交量', '振幅', '涨跌幅', '涨跌额', '换手率'], inplace=True)
        df.rename(columns={'日期': 'Date', '开盘': 'Open'}, inplace=True) # Replace title
        df.rename(columns={'收盘': 'Close', '最高': 'High'}, inplace=True) # Replace title
        df.rename(columns={'最低': 'Low', '成交额': 'Amount'}, inplace=True) # Replace title
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        try:
            if dog_id.find('.') >= 0:
                dog_id = dog_id.split('.')[1]       # 106.XXX -> XXX
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
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except Exception as e:
            log.get().error('Dog[%s] fetch from longport failed: %s'%(dog_id, str(e)))
            return pd.DataFrame()

def get_dog_us_capital_flow(dog_id):
    if dog_id.find('.') >= 0:
        dog_id = dog_id.split('.')[1]       # 106.XXX -> XXX
    try:
        quote_ctx = get_quote_context()
        resp = quote_ctx.capital_distribution("%s.US"%(dog_id))
        df = pd.DataFrame({
            'Date': [(resp.timestamp - datetime.timedelta(hours=8)).date()],
            'Inflow_Lg': [int(resp.capital_in.large) - int(resp.capital_out.large)],
            'Inflow_Mid': [int(resp.capital_in.medium) - int(resp.capital_out.medium)],
            'Inflow_Sm': [int(resp.capital_in.small) - int(resp.capital_out.small)],
        })
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        log.get().error('Dog[%s] capital fetch failed: %s'%(dog_id, str(e)))
        return pd.DataFrame()

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success')

    quantitative_init()

    dog_list = []
    if (args.market == 'us'):
        if not args.test:
            wait_us_market_open(log.get())
        dog_list = get_dog(args.market)
        log.get().info(dog_list)
    elif (args.market == 'cn'):
        dog_list = []
        dog_list = list(set(dog_list).union(get_dog(args.market)))

    # dog_list = ['sh000016']       # Only for test specific dog
    for dog_index in dog_list:
        db, inexist = create_if_market_inexist(dog_index)
        if inexist:
            if (args.market == 'us'):
                dog_full_code = get_fullcode(args.market, dog_index)
                df1 = get_dog_us_daily_hist(dog_full_code)
                if (df1.empty):
                    continue
                df2 = get_dog_us_capital_flow(dog_full_code)
                if (df2.empty):  
                    continue
                else:
                    df = pd.merge(df1, df2, on='Date', how='left')
                    #df.fillna(0, inplace=True)     # do not fill as 0 to aviod over write.
            elif (args.market == 'cn'):
                df1 = get_dog_cn_daily_hist(dog_index)
                if (df1.empty):
                    continue
                df2 = get_dog_cn_capital_flow(dog_index)
                if (df2.empty):
                    df = df1
                else:
                    df = pd.merge(df1, df2, on='Date', how='left')
                    df.fillna(0, inplace=True)      # do not fill as 0 to aviod over write.
        else:
            current_date = datetime.datetime.now().strftime('%Y%m%d')
            start_date = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime('%Y%m%d')    # 10 days ago
            if (args.market == 'us'):
                dog_full_code = get_fullcode(args.market, dog_index)
                df1 = get_dog_us_daily_hist(dog_full_code, start_date=start_date, end_date=current_date)
                if (df1.empty):
                    continue
                df2 = get_dog_us_capital_flow(dog_full_code)
                if (df2.empty):  
                    continue
                else:
                    df = pd.merge(df1, df2, on='Date', how='left')
                    #df.fillna(0, inplace=True)     # do not fill as 0 to aviod over write.
            elif (args.market == 'cn'):
                df1 = get_dog_cn_daily_hist(dog_index, start_date=start_date, end_date=current_date)
                if (df1.empty):
                    continue
                df2 = get_dog_cn_capital_flow(dog_index)
                if (df2.empty):
                    df = df1
                else:
                    df = pd.merge(df1, df2, on='Date', how='left')
                    #df.fillna(0, inplace=True)     # do not fill as 0 to aviod over write.
        dog_update_list = df.to_dict(orient='records')
        # Remove nan value
        for entry in dog_update_list:
            keys_to_remove = [key for key, value in entry.items() if isinstance(value, float) and math.isnan(value)]
            for key in keys_to_remove:
                del entry[key]
        log.get().info('Start insert for [%s]'%(dog_index))
        for dog_update_index in dog_update_list:
            #log.get().info(dog_update_index)
            date_tmp = dog_update_index['Date']
            flag = db.update_dog_market_by_date(dog_index, date_tmp, dog_update_index)
            #flag = db.insert_dog_market(dog_index, dog_update_index)
            if (not flag):
                log.get().info('dog insert failed: %s'%(str(dog_update_index)))

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")
    
    # Append arguments
    parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')
    parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

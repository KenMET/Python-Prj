#!/bin/python3

# System lib
import os, sys
import argparse
import datetime
import requests

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
import adata as ad
sys.path.append(r'%s/../common'%(py_dir))
from database import create_if_sentiment_inexist
from config import get_notify_list, get_adata_key
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

key_dict = {}
def set_limitted(key):
    global key_dict
    key_dict.update({key:False})
def insert_key(key):
    global key_dict
    key_dict.update({key:True})
def init_key():
    key_list = get_adata_key()
    if len(key_list) == 0:
        return False
    for index in key_list:
        insert_key(index)
    return True
def get_next_adata_key(limited_key=None):
    global key_dict
    if limited_key != None:
        set_limitted(limited_key)
    for index in key_dict:
        if key_dict[index] == True:
            return index
    return ''

def get_sentiment(key, dog_id, start, end):
    url = 'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=%s&apikey=%s&time_from=%s&time_to=%s'%(dog_id, key, start, end)
    r = requests.get(url)
    data = r.json()
    return data

def is_up_limit(data):
    information = data.get('Information', '')
    if information.find('remove all daily rate limits') >= 0:
        log.get().info('Adata key up to daily limit...')
        return True
    return False

# "sentiment_score_definition": 
#   x <= -0.35: Bearish
#   -0.35 < x <= -0.15: Somewhat-Bearish
#   -0.15 < x < 0.15: Neutral
#   0.15 <= x < 0.35: Somewhat_Bullish
#   x >= 0.35: Bullish
# "relevance_score_definition": "0 < x <= 1, with a higher score indicating higher relevance.",

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='w', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success')

    if (not init_key()):
        log.get().error('Adata key null, sentiment fetch failed...')
        return 
    end_date = datetime.datetime.now().strftime('%Y%m%dT2359')
    start_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y%m%dT0000')    # 1 days ago

    adata_key = get_next_adata_key()
    db = create_if_sentiment_inexist()
    dog_list = get_notify_list('us')    # support us for now...
    for dog_code in dog_list:
        data = get_sentiment(adata_key, dog_code, start_date, end_date)
        if is_up_limit(data):
            adata_key = get_next_adata_key(adata_key)
        feed = data.get('feed', [])
        if len(feed) == 0:
            log.get().info('Sentiment fetch failed due to nothing new: %s'%(dog_code))
            continue
        score_list = []
        for index in feed:
            title = index['title']
            summary = index['summary']
            time_published = index['time_published']
            overall_sentiment_score = index['overall_sentiment_score']
            score_list.append(float(overall_sentiment_score))
            tmp_dict = {
                'Title': title,
                'Code': dog_code,
                'Summary': summary,
                'PublishTime': time_published,
                'Score': overall_sentiment_score,
            }
            db.insert_sentiment(tmp_dict)
            log.get().info('Fetched new sentiment: %s'%(str(tmp_dict)))
        sorted_score_list = sorted(score_list)
        log.get().info('score list[%s]:%s'%(dog_code, str(sorted_score_list)))
        #remove_min_max_count = int(len(feed) * 0.1)     # remove 10%(min&max) of sentiment length
        #trimmed_data = sorted_score_list[remove_min_max_count:-remove_min_max_count]
        #log.get().info(trimmed_data)
        #score_avg = sum(trimmed_data) / len(trimmed_data)
        #log.get().info('Score Avg[%s]: %.2f'%(start, score_avg))
    db.closeSession()

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for dog info fetch")
    
    # Append arguments
    parser.add_argument('--start', type=str, default='', help='Start Date, for example: 20241001')
    parser.add_argument('--end', type=str, default='', help='End Date, null as today')
    parser.add_argument('--target', type=str, default='', help='Backtest dog name')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)

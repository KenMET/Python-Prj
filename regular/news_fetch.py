import hashlib
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
sys.path.append(r'%s/../mail'%(py_dir))
sys.path.append(r'%s/../mysql'%(py_dir))
sys.path.append(r'%s/../spider'%(py_dir))
sys.path.append(r'%s/../notification'%(py_dir))
sys.path.append(r'%s/../common_api/xml_operator'%(py_dir))

import db_news as cbn
import xml_operator as xo
import spider_request as srq
import notification as notify

# '161725'
def main(logger):
    file_name = '%s/config.xml'%(py_dir)
    cfg = xo.operator(file_name)
    cfg_dict = cfg.walk_node(cfg.root_node)
    news_config_dict = cfg_dict.get('news_config', {})

    db = cbn.newsdb()
    tables = db.queryTable()
    if 'top_news' not in tables:
        db.create_top_news_table()

    news_list = srq.request_top_news(60)
    for new_index in news_list:
        time.sleep(1)
        news_full_dict = {}
        news_full_dict.update(new_index)
        news_url = news_full_dict['Url']
        content = srq.request_top_news_content(news_url)
        if (content == ""):
            bark_obj = notify.bark()
            flag = bark_obj.send_title_content('Spider Top News', 'Content fetch failed[%s]'%(news_full_dict['Title']))
            logger.info('Content fetch failed[bark:%s]:%s, title:%s'%(str(flag), news_full_dict['Url'], news_full_dict['Title']))
        news_full_dict.update({'OriginContent':content})
        flag = db.insertTopNews(news_full_dict)
        logger.info('insert[%s], [%s]Title:%s'%(str(flag), news_full_dict['Time'], news_full_dict['Title']))

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_name = py_dir + '/' + py_name + '.log'
    fh = logging.FileHandler(log_name, mode='w')    # a == append,  w == overwrite
    fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('Logger Creat Success')
    #logger.debug("this is debug") # Enable to modify fh.setLevel(logging.INFO) to logging.DEDBUG
    #logger.warning("this is warning")
    #logging.error("this is error")
    main(logger)

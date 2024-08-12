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
sys.path.append(r'%s/../mysql'%(py_dir))
import db_cat as dbc
import db_dog as dbd
import db_news as dbn
sys.path.append(r'%s/../spider'%(py_dir))
import spider_request as srq
sys.path.append(r'%s/../notification'%(py_dir))
import notification as notify
sys.path.append(r'%s/../common_api/xml_operator'%(py_dir))
import xml_operator as xo

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False

# Not know how to sanity yet...........
def cat_survey(logger, db, table_name):
    ret = db.queryCatAll()
    for index in ret:
        temp_dict = db.get_dict_from_obj(index)
        #print (temp_dict)
    return True

def cat_net_rt(logger, db, table_name):
    ret = db.queryLastCatRT(table_name.replace('cat_net_rt_', ''))
    temp_dict = db.get_dict_from_obj(ret)
    NetValueTime = temp_dict.get('NetValueTime')
    if NetValueTime == None:
        logger.info("%s [NetValueTime] return None"%(table_name))
        return False
    else:
        if type(NetValueTime) != datetime.date:
            logger.info("%s [NetValueTime] type incorrect[%s]"%(table_name, str(type(NetValueTime))))
            return False
    del temp_dict['NetValueTime']
    del temp_dict['Reserve']
    for number_index in temp_dict:
        number_str = temp_dict.get(number_index)
        if number_str == None:
            logger.info("%s [%s] return None"%(table_name, number_index))
            return False
        if (number_str.find('(') > 0):
            number_str = number_str[:number_str.find('(')]
        if (not is_number(number_str.replace('%', '').replace(',', ''))):
            logger.info("%s [%s] is not a number[%s]"%(table_name, number_index, number_str))
            return False
    return True

def cat_holding(logger, db, table_name):
    file_name = '%s/config.xml'%(py_dir)
    cfg = xo.operator(file_name)
    cfg_dict = cfg.walk_node(cfg.root_node)
    skip_cat_list = cfg_dict.get('sanity_config', {}).get('skip_cat', {}).get('id', [])
    cat_code = table_name.replace('cat_holding_', '')
    if cat_code in skip_cat_list:
        return True

    ret = db.queryLastCatHolding(cat_code)
    temp_dict = db.get_dict_from_obj(ret)
    if temp_dict == None:
        logger.info("%s [queryLastCatHolding] return dict None"%(table_name))
        return False
    DogCodeQuarter = temp_dict.get('DogCodeQuarter')
    if DogCodeQuarter == None:
        logger.info("%s [DogCodeQuarter] return dict None"%(table_name))
        return False
    else:
        if type(DogCodeQuarter) != type('string'):
            logger.info("%s [NetValueTime] type incorrect[%s]"%(table_name, str(type(DogCodeQuarter))))
            return False
        if (len(DogCodeQuarter) != len('2015-09-30:300017')):
            logger.info("%s [DogCodeQuarter] length incorrect[%s]"%(table_name, str(len(DogCodeQuarter))))
            return False
    del temp_dict['DogCodeQuarter']
    DogName = temp_dict.get('DogName')
    if DogName == None:
        logger.info("%s [DogName] return None"%(table_name))
        return False
    else:
        if type(DogCodeQuarter) != type('string'):
            logger.info("%s [DogName] type incorrect[%s]"%(table_name, str(type(DogCodeQuarter))))
            return False
    del temp_dict['DogName']
    for number_index in temp_dict:
        number_str = temp_dict.get(number_index)
        if number_str == None:
            logger.info("%s [%s] return None"%(table_name, number_index))
            return False
        if (number_str.find('(') > 0):
            number_str = number_str[:number_str.find('(')]
        if (not is_number(number_str.replace('%', '').replace(',', ''))):
            logger.info("%s [%s] is not a number[%s]"%(table_name, number_index, number_str))
            return False
    return True, None

def cat_net(logger, db, table_name):
    ret = db.queryLastCatNet(table_name.replace('cat_net_', ''))
    temp_dict = db.get_dict_from_obj(ret)
    NetValueDate = temp_dict.get('NetValueDate')
    if NetValueDate == None:
        logger.info("%s [NetValueDate] return None"%(table_name))
        return False
    else:
        if type(NetValueDate) != datetime.date:
            logger.info("table_name [NetValueDate] type incorrect[%s]"%(str(type(NetValueDate))))
            return False
    del temp_dict['NetValueDate']
    SubscriptionStatus = temp_dict.get('SubscriptionStatus')
    if SubscriptionStatus == None:
        logger.info("%s [SubscriptionStatus] return None"%(table_name))
        return False
    else:
        if type(SubscriptionStatus) != type('string'):
            logger.info("table_name [SubscriptionStatus] type incorrect[%s]"%(str(type(SubscriptionStatus))))
            return False
    del temp_dict['SubscriptionStatus']
    RedemptionStatus = temp_dict.get('RedemptionStatus')
    if RedemptionStatus == None:
        logger.info("%s [RedemptionStatus] return None"%(table_name))
        return False
    else:
        if type(RedemptionStatus) != type('string'):
            logger.info("table_name [RedemptionStatus] type incorrect[%s]"%(str(type(RedemptionStatus))))
            return False
    del temp_dict['RedemptionStatus']
    del temp_dict['DividendsSending']
    del temp_dict['Reserve']
    for number_index in temp_dict:
        number_str = temp_dict.get(number_index)
        if number_str == None:
            logger.info("%s [%s] return None"%(table_name, number_index))
            return False
        if (number_str.find('(') > 0):
            number_str = number_str[:number_str.find('(')]
        if (not is_number(number_str.replace('%', '').replace(',', ''))):
            logger.info("%s [%s] is not a number[%s]"%(table_name, number_index, number_str))
            return False
    return True

def dog_money_flow(logger, db, table_name):
    ret = db.queryLastDogMoneyFlow(table_name.replace('dog_money_flow_', ''))
    temp_dict = db.get_dict_from_obj(ret)
    Date = temp_dict.get('Date')
    if Date == None:
        logger.info("%s [Date] return None"%(table_name))
        return False
    else:
        if type(Date) != datetime.datetime:
            logger.info("%s [Date] type incorrect[%s]"%(table_name, str(type(Date))))
            return False
    del temp_dict['Date']
    for number_index in temp_dict:
        number_str = temp_dict.get(number_index)
        if number_str == None:
            logger.info("%s [%s] return None"%(table_name, number_index))
            return False
        if (not is_number(number_str)):
            logger.info("%s [%s] is not a number[%s]"%(table_name, number_index, number_str))
            return False
    return True

def top_news(logger, db):
    ret = db.queryLastNew()
    temp_dict = db.get_dict_from_obj(ret)
    Time = temp_dict.get('Time')
    if Time == None:
        logger.info("Top_news [Time] return None")
        return False, "Top_news [Time] return None"
    else:
        if type(Time) != datetime.datetime:
            logger.info("[Time] type incorrect[%s]"%(str(type(Time))))
            return False, "[Time] type incorrect[%s]"%(str(type(Time)))
        if (datetime.datetime.now()-Time) > datetime.timedelta(days=1):
            logger.info("[Time] latest update over 1 day [%s]"%(str(type(Time))))
            return False, "[Time] latest update over 1 day [%s]"%(str(type(Time)))
    return True, ''

def cat_sanity(logger):
    db = dbc.catdb('kanos_cat')
    tables = db.queryTable()
    for table_index in tables:
        if (table_index.find('survey') >= 0):
            flag = cat_survey(logger, db, table_index)
            if (not flag):
                return flag, 'CatSurvey Sanity failed'
        elif (table_index.find('net_rt') >= 0 and is_number(table_index.replace('cat_net_rt_', ''))):
            flag = cat_net_rt(logger, db, table_index)
            if (not flag):
                return flag, 'Cat[%s] Sanity failed'%(table_index)
        elif (table_index.find('holding') >= 0):
            flag = cat_holding(logger, db, table_index)
            if (not flag):
                return flag, 'Cat[%s] Sanity failed'%(table_index)
        elif (table_index.find('net') >= 0 and is_number(table_index.replace('cat_net_', ''))):
            flag = cat_net(logger, db, table_index)
            if (not flag):
                return flag, 'Cat[%s] Sanity failed'%(table_index)
    return True, ''

def dog_sanity(logger):
    db = dbd.dogdb('kanos_dog')
    tables = db.queryTable()
    for table_index in tables:
        if (table_index.find('money_flow') >= 0):
            flag = dog_money_flow(logger, db, table_index)
            if (not flag):
                return flag, 'Dog[%s] Sanity failed'%(table_index)
    return True, ''

def news_sanity(logger):
    db = dbn.newsdb('kanos_news')
    tables = db.queryTable()
    for table_index in tables:
        if (table_index.find('top_news') >= 0):
            flag, error = top_news(logger, db)
            if (not flag):
                return flag, 'TopNews Sanity failed:%s'%(error)
    return True, ''

def main(logger):
    content = ''
    flag, error = cat_sanity(logger)
    if (not flag):
        content += error + '\n'
    else:
        logger.info('Cat Database sanity pass!')

    flag, error = dog_sanity(logger)
    if (not flag):
        content += error + '\n'
    else:
        logger.info('Dog Database sanity pass!')

    flag, error = news_sanity(logger)
    if (not flag):
        content += error + '\n'
    else:
        logger.info('News Database sanity pass!')

    if (len(content) == 0):
        content = 'All database works normal. ^_^ '
    bark_obj = notify.bark()
    flag = bark_obj.send_title_content('Spider Sanity', content)
    logger.info('Bark Notification Result[%s]'%(str(flag)))

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_name = py_dir + '/' + py_name + '.log'
    fh = logging.FileHandler(log_name, mode='w')
    fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('Logger Creat Success')
    main(logger)



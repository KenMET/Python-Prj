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
sys.path.append(r'%s/../common_api/xml_operator'%(py_dir))
import mail
import db_cat as cbc
import db_dog as cbd
import xml_operator as xo
import spider_request as srq

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
    return True, None

def cat_net_rt(logger, db, table_name):
    ret = db.queryLastCatRT(table_name.replace('cat_net_rt_', ''))
    temp_dict = db.get_dict_from_obj(ret)
    NetValueTime = temp_dict.get('NetValueTime')
    if NetValueTime == None:
        return False, "%s [NetValueTime] return None"%(table_name)
    else:
        if type(NetValueTime) != datetime.date:
            return False, "table_name [NetValueTime] type incorrect[%s]"%(str(type(NetValueTime)))
    del temp_dict['NetValueTime']
    del temp_dict['Reserve']
    for number_index in temp_dict:
        number_str = temp_dict.get(number_index)
        if number_str == None:
            return False, "%s [%s] return None"%(table_name, number_index)
        if (number_str.find('(') > 0):
            number_str = number_str[:number_str.find('(')]
        if (not is_number(number_str.replace('%', '').replace(',', ''))):
            return False, "%s [%s] is not a number[%s]"%(table_name, number_index, number_str)
    return True, None

def cat_holding(logger, db, table_name):
    ret = db.queryLastCatHolding(table_name.replace('cat_holding_', ''))
    temp_dict = db.get_dict_from_obj(ret)
    DogCodeQuarter = temp_dict.get('DogCodeQuarter')
    if DogCodeQuarter == None:
        return False, "%s [DogCodeQuarter] return None"%(table_name)
    else:
        if type(DogCodeQuarter) != type('string'):
            return False, "table_name [NetValueTime] type incorrect[%s]"%(str(type(DogCodeQuarter)))
        if (len(DogCodeQuarter) != len('2015-09-30:300017')):
            return False, "table_name [DogCodeQuarter] length incorrect[%s]"%(str(len(DogCodeQuarter)))
    del temp_dict['DogCodeQuarter']
    DogName = temp_dict.get('DogName')
    if DogName == None:
        return False, "%s [DogName] return None"%(table_name)
    else:
        if type(DogCodeQuarter) != type('string'):
            return False, "table_name [DogName] type incorrect[%s]"%(str(type(DogCodeQuarter)))
    del temp_dict['DogName']
    for number_index in temp_dict:
        number_str = temp_dict.get(number_index)
        if number_str == None:
            return False, "%s [%s] return None"%(table_name, number_index)
        if (number_str.find('(') > 0):
            number_str = number_str[:number_str.find('(')]
        if (not is_number(number_str.replace('%', '').replace(',', ''))):
            return False, "%s [%s] is not a number[%s]"%(table_name, number_index, number_str)
    return True, None

def cat_net(logger, db, table_name):
    ret = db.queryLastCatNet(table_name.replace('cat_net_', ''))
    temp_dict = db.get_dict_from_obj(ret)
    NetValueDate = temp_dict.get('NetValueDate')
    if NetValueDate == None:
        return False, "%s [NetValueDate] return None"%(table_name)
    else:
        if type(NetValueDate) != datetime.date:
            return False, "table_name [NetValueDate] type incorrect[%s]"%(str(type(NetValueDate)))
    del temp_dict['NetValueDate']
    SubscriptionStatus = temp_dict.get('SubscriptionStatus')
    if SubscriptionStatus == None:
        return False, "%s [SubscriptionStatus] return None"%(table_name)
    else:
        if type(SubscriptionStatus) != type('string'):
            return False, "table_name [SubscriptionStatus] type incorrect[%s]"%(str(type(SubscriptionStatus)))
    del temp_dict['SubscriptionStatus']
    RedemptionStatus = temp_dict.get('RedemptionStatus')
    if RedemptionStatus == None:
        return False, "%s [RedemptionStatus] return None"%(table_name)
    else:
        if type(RedemptionStatus) != type('string'):
            return False, "table_name [RedemptionStatus] type incorrect[%s]"%(str(type(RedemptionStatus)))
    del temp_dict['RedemptionStatus']
    del temp_dict['DividendsSending']
    del temp_dict['Reserve']
    for number_index in temp_dict:
        number_str = temp_dict.get(number_index)
        if number_str == None:
            return False, "%s [%s] return None"%(table_name, number_index)
        if (number_str.find('(') > 0):
            number_str = number_str[:number_str.find('(')]
        if (not is_number(number_str.replace('%', '').replace(',', ''))):
            return False, "%s [%s] is not a number[%s]"%(table_name, number_index, number_str)
    return True, None

def cat_sanity(logger):
    db = cbc.catdb()
    tables = db.queryTable()
    for table_index in tables:
        if (table_index.find('survey') > 0):
            flag, error = cat_survey(logger, db, table_index)
            if (not flag):
                return flag, error
        elif (table_index.find('net_rt') > 0 and is_number(table_index.replace('cat_net_rt_', ''))):
            flag, error = cat_net_rt(logger, db, table_index)
            if (not flag):
                return flag, error
        elif (table_index.find('holding') > 0):
            flag, error = cat_holding(logger, db, table_index)
            if (not flag):
                return flag, error
        elif (table_index.find('net') > 0 and is_number(table_index.replace('cat_net_', ''))):
            flag, error = cat_net(logger, db, table_index)
            if (not flag):
                return flag, error
    return True, None

def dog_money_flow(logger, db, table_name):
    ret = db.queryLastDogMoneyFlow(table_name.replace('dog_money_flow_', ''))
    temp_dict = db.get_dict_from_obj(ret)
    Date = temp_dict.get('Date')
    if Date == None:
        return False, "%s [Date] return None"%(table_name)
    else:
        if type(Date) != datetime.datetime:
            return False, "table_name [Date] type incorrect[%s]"%(str(type(Date)))
    del temp_dict['Date']
    for number_index in temp_dict:
        number_str = temp_dict.get(number_index)
        if number_str == None:
            return False, "%s [%s] return None"%(table_name, number_index)
        if (not is_number(number_str)):
            return False, "%s [%s] is not a number[%s]"%(table_name, number_index, number_str)
    return True, None

def dog_sanity(logger):
    db = cbd.dogdb()
    tables = db.queryTable()
    tables = db.queryTable()
    for table_index in tables:
        if (table_index.find('money_flow') > 0):
            flag, error = dog_money_flow(logger, db, table_index)
            if (not flag):
                return flag, error
    return True, None


def main(logger):
    flag, error = cat_sanity(logger)
    email_send_flag = False
    content = ''
    if (not flag):
        logger.info('Cat Database sanity failed!')
        logger.info(error)
        content = 'Cat Database sanity failed! Failed reason:\n'+error+'\n'
        email_send_flag = True
    else:
        logger.info('Cat Database sanity pass!')
    flag, error = dog_sanity(logger)
    if (not flag):
        logger.info('Dog Database sanity failed!')
        logger.info(error)
        content += 'Dog Database sanity failed! Failed reason:\n'+error+'\n'
        email_send_flag = True
    else:
        logger.info('Dog Database sanity pass!')

    if (email_send_flag):
        mail_obj = mail.mail()
        subject = 'This is KenStation Database Sanity email'
        content_type = 'plain' # or 'html'
        mail_obj.set_content('ken_processor@outlook.com', subject, content, content_type)
        flag = mail_obj.send()
        logger.info('Mail Send Result[%s]'%(str(flag)))

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
    main(logger)



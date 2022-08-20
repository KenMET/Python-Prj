import hashlib
import os, sys
import json
import logging
import tempfile
import optparse
import datetime, time, calendar
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
import xml_operator as xo
import spider_request as srq

def is_work_day():
    currentdate = datetime.date.today()
    currentday =calendar.weekday(currentdate.year, currentdate.month, currentdate.day)
    if currentday >= 5: # 0 equl to monday
        return False
    return True

def is_cat_running():
    time_range = [
        {'start':"09:30:00", 'end':"12:00:00"},
        {'start':"13:00:00", 'end':"15:00:00"},
    ]
    now = datetime.datetime.now()
    start_time = datetime.datetime.strptime(str(datetime.datetime.now().date()) + '09:30', '%Y-%m-%d%H:%M')
    end_time = datetime.datetime.strptime(str(datetime.datetime.now().date()) + '11:30', '%Y-%m-%d%H:%M')
    if (now < start_time):
        return -1 # before start
    elif (now < end_time):
        return 0 # during time range
    
    start_time2 = datetime.datetime.strptime(str(datetime.datetime.now().date()) + '13:00', '%Y-%m-%d%H:%M')
    end_time2 = datetime.datetime.strptime(str(datetime.datetime.now().date()) + '15:00', '%Y-%m-%d%H:%M')
    if (now < start_time2):
        return 1 # Waiting
    elif (now < end_time2):
        return 0 # during time range
    return 2 # No need to update, exit

def update_cat(logger):
    if (not is_work_day()):
        logger.info('Not a workday, skip...')
        return
    file_name = '%s/config.xml'%(py_dir)
    cfg = xo.operator(file_name)
    cfg_dict = cfg.walk_node(cfg.root_node)
    cat_list = cfg_dict.get('cat_list', {}).get('id', [])
    db = cbc.catdb()
    tables = db.queryTable()

    ret = is_cat_running()
    if (ret == -1):
        for cat_index in cat_list:
            net_table_name = 'cat_net_rt_%s'%(cat_index)
            if (net_table_name not in tables):
                continue
            ret = db.deleteCatRTByID(cat_index)
            logger.info ('[Info] - Empty the cat rt table')
    elif (ret == 2):
        logger.info ('[Info] - No need to run')
        return

    while True:
        time.sleep(58)
        ret = is_cat_running()
        if (ret == 1 or ret == -1):
            continue
        elif (ret == 2):
            break
        for cat_index in cat_list:
            temp_dict = srq.request_daily2(cat_index)

            net_table_name = 'cat_net_rt_%s'%(cat_index)
            if (net_table_name not in tables):
                db.create_net_rt_table(net_table_name)
                logger.info('Create table[%s]'%(net_table_name))
            del temp_dict['ID']

            date_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            temp_dict.update({'NetValueTime': date_now})

            logger.info('Table[%s] update net RT:%s'%(net_table_name, str(temp_dict)))
            flag = db.insertCatNetRT(cat_index, temp_dict)
            if (not flag):
                flag = db.updateCatNetByTime(cat_index, date_now, temp_dict)
                if (not flag):
                    logger.info ('[Error] - CatNetRT update failed')

    mail_obj = mail.mail()
    subject = 'This is KenStation Test email'
    content = 'This is Test data:\nUpdate daily net RT done'
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
    update_cat(logger)

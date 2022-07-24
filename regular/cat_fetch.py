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
sys.path.append(r'%s/../spider'%(py_dir))
sys.path.append(r'%s/../common_api/xml_operator'%(py_dir))
import db_cat as cbc
import xml_operator as xo
import spider_request as srq

def update(logger):
    file_name = '%s/config.xml'%(py_dir)
    cfg = xo.operator(file_name)
    cfg_dict = cfg.walk_node(cfg.root_node)
    cat_list = cfg_dict.get('cat_list', {}).get('id', [])
    db = cbc.catdb()
    tables = db.queryTable()

    for cat_index in cat_list:
        temp_dict = srq.request_base(cat_index)
        flag = db.insertCatSurvey(temp_dict)
        if (not flag):
            id = temp_dict['ID']
            del temp_dict['ID']
            logger.info('Table[CatSurvey] id[%s] update: %s'%(id, str(cat_index)))
            flag = db.updateCatSurveyByID(id, temp_dict)
            if (not flag):
                logger.info ('[Error] - CatSurvey update failed')
        
        net_count = 5
        net_table_name = 'cat_net_%s'%(cat_index)
        if (net_table_name not in tables):
            db.create_table(net_table_name)
            est_date_str = temp_dict['EstablishmentDate_Size'][:temp_dict['EstablishmentDate_Size'].find('/')].strip(' \r\n')
            date_est = datetime.datetime.strptime(est_date_str, '%Y年%m月%d日')
            date_now = datetime.datetime.now()
            delta_days = int((date_now - date_est).days * 5 / 7)
            net_count = delta_days
            logger.info('Create table[%s]'%(net_table_name))
        temp_list = srq.request_net(cat_index, net_count)
        logger.info('Table[%s] insert net [%d] row'%(net_table_name, len(temp_list)))
        for net_index in temp_list:
            logger.info('Table[%s] update net:%s'%(net_table_name, str(net_index)))
            flag = db.insertCatNet(cat_index, net_index)
            if (not flag):
                date = net_index['NetValueDate']
                del net_index['NetValueDate']
                flag = db.updateCatNetByDate(cat_index, date, net_index)
                if (not flag):
                    logger.info ('[Error] - CatNet update failed')


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
    update(logger)

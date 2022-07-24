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
import xml_operator as xo
import spider_request as srq

def update_cat(logger):
    file_name = '%s/config.xml'%(py_dir)
    cfg = xo.operator(file_name)
    cfg_dict = cfg.walk_node(cfg.root_node)
    cat_list = cfg_dict.get('cat_list', {}).get('id', [])
    db = cbc.catdb()
    tables = db.queryTable()

    mail_obj = mail.mail()
    subject = 'This is KenStation Test email'
    content = 'This is Test data:\n'
    content_type = 'plain' # or 'html'

    for cat_index in cat_list:
        temp_dict = srq.request_daily(cat_index)
        content += str(temp_dict)
        content += '\n********************\n'

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

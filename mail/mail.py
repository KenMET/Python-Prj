#!/usr/bin/ python3

import os, sys
import logging
import datetime, time
import threading, multiprocessing, subprocess
import smtplib
from email.mime.text import MIMEText
from email.header import Header

py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))


class mail() :
    def __init__(self,
            host = 'smtp.qq.com',
            port = 465,
            sender = '465116954@qq.com',
            access_key = 'gqsmdvnieobkbjfj'):
        self.host = host
        self.sender = sender
        self.access_key = access_key
        self.obj = smtplib.SMTP_SSL(host, port)
        self.obj.login(sender, access_key)

    def set_content(self, dst, subject, content, type):
        self.dst = dst
        self.message = MIMEText(content, type, 'utf-8')
        self.message['Subject'] = Header(subject, 'utf-8')
        self.message['From'] = self.sender
        self.message['To'] = dst
    
    def send(self):
        try:
            self.obj.sendmail(self.sender, self.dst, self.message.as_string())
        except Exception as e:
            print ('Mail send failed:' + str(e))
            return False
        return True

if __name__ == '__main__':
    pass
    mail_obj = mail()
    subject = 'This is KenStation Test email'
    content = 'This is Test data(3), Do not reply this email!'
    content_type = 'plain' # or 'html'
    mail_obj.set_content('ken_processor@outlook.com', subject, content, content_type)
    mail_obj.send()

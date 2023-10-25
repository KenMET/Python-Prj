#!/usr/bin/ python3

import os, sys
import logging
import datetime, time
import threading, multiprocessing, subprocess
import smtplib
import requests
from email.mime.text import MIMEText
from email.header import Header

py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../common_api/xml_operator'%(py_dir))

import xml_operator as xo

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

class bark() :
    def __init__(self):
        cfg = xo.operator('%s/config.xml'%(py_dir))
        self.server = cfg.walk_node(cfg.root_node).get('server', '')
        self.key_list = cfg.walk_node(cfg.root_node).get('key_list', {}).get('id', [])
        if type(self.key_list) == type(''):
            self.key_list = [self.key_list, ]
        #print (self.server)
        #print (self.key_list)
    
    def is_server_avaliable(self):
        if self.server == '':
            return False
        return True

    def send_content(self, content='default'):
        if (not self.is_server_avaliable()):
            return False
        for key_index in self.key_list:
            api_url = self.server + '/' + key_index + '/' + content
            #print (api_url)
            requests.get(api_url)
        return True

    def send_title_content(self, title='bark', content='default'):
        if (not self.is_server_avaliable()):
            return False
        for key_index in self.key_list:
            api_url = self.server + '/' + key_index + '/' + title + '/' + content
            #print (api_url)
            requests.get(api_url)
        return True

    def send_bell(self, bell, title='bark', content='default'):
        if (not self.is_server_avaliable()):
            return False
        for key_index in self.key_list:
            api_url = self.server + '/' + key_index + '/' + title + '/' + content + '?sound=' + bell
            #print (api_url)
            requests.get(api_url)
        return True

    def send_icon(self, icon, title='bark', content='default'):
        if (not self.is_server_avaliable()):
            return False
        for key_index in self.key_list:
            api_url = self.server + '/' + key_index + '/' + title + '/' + content + '?icon=' + icon
            #print (api_url)
            requests.get(api_url)
        return True

    def send_timeliness_notice(self, level, title='bark', content='default'):
        if (not self.is_server_avaliable()):
            return False
        for key_index in self.key_list:
            api_url = self.server + '/' + key_index + '/' + title + '/' + content + '?level=' + level
            #print (api_url)
            requests.get(api_url)
        return True

#<ServerAddr>/jTLWptdK8JHKM7syGh2w8D/这里改成你自己的推送内容
#<ServerAddr>/jTLWptdK8JHKM7syGh2w8D/推送标题/这里改成你自己的推送内容
#<ServerAddr>/jTLWptdK8JHKM7syGh2w8D/推送铃声?sound=minuet
#<ServerAddr>/jTLWptdK8JHKM7syGh2w8D/自定义推送图标（需iOS15或以上）?icon=https://day.app/assets/images/avatar.jpg
#<ServerAddr>/jTLWptdK8JHKM7syGh2w8D/时效性通知?level=timeSensitive

if __name__ == '__main__':
    #mail_obj = mail()
    #subject = 'This is KenStation Test email'
    #content = 'This is Test data(3), Do not reply this email!'
    #content_type = 'plain' # or 'html'
    #mail_obj.set_content('ken_processor@outlook.com', subject, content, content_type)
    #mail_obj.send()
    
    bark_obj = bark()
    bark_obj.send_content('Here is content')
    time.sleep(3)
    bark_obj.send_title_content('Here is title1', 'Here is content2')
    time.sleep(3)
    bark_obj.send_bell('minuet', 'Here is title2', 'Here is content3')
    time.sleep(3)
    bark_obj.send_icon('https://day.app/assets/images/avatar.jpg', 'Here is title3', 'Here is content4')
    time.sleep(3)
    bark_obj.send_timeliness_notice('timeSensitive', 'Here is title4', 'Here is content5')

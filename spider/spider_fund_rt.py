import time
import datetime
import sys
import gc
import copy
import logging
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


py_dir = '/home/ken/Code/Python-Prj'
sys.path.append(r'%s/mysql/'%(py_dir))
import mysql_lib as ml

rt_web = 'http://fund.eastmoney.com/xxxxxx.html'



def spider_init(*args):
    chrome_options=Options()
    for index in args:
        chrome_options.add_argument(index)
    return webdriver.Chrome(chrome_options=chrome_options)


def fund_get_info(driver, fund_code):
    if fund_code == '' or fund_code == None:
        return {}
    driver.get(rt_web.replace('xxxxxx', fund_code))
    info_str = driver.find_element_by_class_name("dataOfFund").text
    rt_list = info_str.split('\n')
    rt_time = rt_list[0].replace('净值估算','')
    rt_rise_val = round(float(rt_list[2]), 6)
    rt_rise_per = round(float(rt_list[3].strip('%')) / 100, 6)
    return {rt_time:[rt_rise_val, rt_rise_per]}


def main_process(code_list):
    dict_code = {}
    chrome_args = ['--no-sandbox', '--disable-dev-shm-usage', '--headless']
    driver = spider_init(*chrome_args)
    for i in range(2 * 30):
        for code_index in code_list:
            dict_code.update({code_index:{}})
            tmp_dict = fund_get_info(driver, code_index)
            dict_code[code_index].update(tmp_dict)
        time.sleep(30)
        print (dict_code)
    
    driver.quit()


if __name__ == '__main__':
    file_argv = sys.argv
    del file_argv[0]
    if len(file_argv) < 1:
        print ('argv error')
        exit()

    th = threading.Thread(target=main_process, args=(file_argv, ))
    th.start()
    th.join()









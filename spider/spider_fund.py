import time
import datetime
import sys
import gc
import copy
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


py_dir = '/home/ken/Code/Python-Prj'
sys.path.append(r'%s/mysql/'%(py_dir))
import mysql_lib as ml

web_dict = {
    '基金基本概况':{'web':'http://fundf10.eastmoney.com/jbgk_xxxxxx.html', 'type':'0'},
    '基金往日数据':{'web':'http://fundf10.eastmoney.com/jjjz_xxxxxx.html', 'type':'1'},
}


base_list_name = [
    '基金全称', '成立日期', '成立规模', '资产规模', '基金管理','累计单位净值', '近1月涨跌', 
    '净值详细数据', '日期', '单位净值', '累计净值', '日涨跌幅', '舆论'
]


class FundBase:
    def __init__(self, Name=None, 
                    Code=None, 
                    Detail = {
                        base_list_name[0]:'',
                        base_list_name[1]:'',
                        base_list_name[2]:'',
                        base_list_name[3]:'',
                        base_list_name[4]:'',
                        base_list_name[5]:'',
                        base_list_name[6]:'',
                        base_list_name[7]:{
                            '1970/01/01/四': {
                                '涨跌幅':'',
                                '单位净值':'',
                            }
                        }
                    }):
        self.Name = Name
        self.Code = Code
        del Detail[base_list_name[7]]
        Detail.update({base_list_name[7]:{}})
        self.Detail = Detail

def spider_init(*args):
    chrome_options=Options()
    for index in args:
        chrome_options.add_argument(index)
    return webdriver.Chrome(chrome_options=chrome_options)

def fund_update_base_info(mysql_obj, fund):
    base_dict = fund.Detail
    total_db = {base_list_name[0]:fund.Name, 
                '基金代码':fund.Code,
                base_list_name[1]:'', 
                base_list_name[2]:'', 
                base_list_name[3]:'', 
                base_list_name[4]:'', 
                }
    title_list = []
    list_tmp = []
    for index in total_db:
        title_list.append(index)
        list_tmp.append(base_dict.get(index, total_db[index]))
    
    #mysql_obj.delet_db('Fund')
    #mysql_obj.creat_db('Fund')
    mysql_obj.select_db('Fund')
    mysql_obj.creat_tb('InfoSummary', total_db)
    mysql_obj.insert('InfoSummary', title_list, [tuple(list_tmp)], True)

def fund_update_net_info(mysql_obj, fund):
    base_dict = fund.Detail[base_list_name[7]]
    total_db = {base_list_name[8]:'', 
                base_list_name[9]:'',
                base_list_name[10]:'',
                base_list_name[11]:'', 
                base_list_name[12]:'', 
                }
    title_list = []
    list_tmp = []
    for index in total_db:
        title_list.append(index)
    for index in base_dict:
        list_tmp.append(tuple([index] + base_dict.get(index, ['NULL']) + ['Not Ready']))
    
    #mysql_obj.delet_db('Fund')
    #mysql_obj.creat_db('Fund')
    mysql_obj.select_db('Fund')
    mysql_obj.creat_tb('NetOf_%s'%(fund.Code), total_db)
    mysql_obj.insert('NetOf_%s'%(fund.Code), title_list, list_tmp, True)

def cleaning_fund_base_info(info_str):
    import re
    import datetime
    dict_info = {}
    data = re.split(r"['\n',' ']", info_str)
    while '' in data:
        data.remove('')
    dict_info.update({base_list_name[0]:data[data.index('基金全称') + 1]})
    dict_info.update({base_list_name[1]:data[data.index('成立日期/规模') + 1]})
    dict_info.update({base_list_name[2]:data[data.index('成立日期/规模') + 3]})
    dict_info.update({base_list_name[3]:data[data.index('资产规模') + 1]})
    dict_info.update({base_list_name[4]:data[data.index('基金管理人') + 1] +'/'+ data[data.index('基金经理人') + 1]})
    TheNewestDay = data.index('分红送配') + 1
    dict_info.update({base_list_name[5]:data[TheNewestDay + 2]})
    tmp_detail = {}
    for i in range(20):
        CurrentTime = data[TheNewestDay]
        #there element need get[单位净值, 累计净值, 日涨跌幅]
        tmp_detail.update({CurrentTime:[data[TheNewestDay + 1], data[TheNewestDay + 2], data[TheNewestDay + 3]]})
        TheNewestDay += 6
    dict_info.update({base_list_name[7]:tmp_detail})
    
    return dict_info


def fund_get_info(driver, fund):
    if fund.Code == None:
        return {}
    driver.get(web_dict['基金往日数据']['web'].replace('xxxxxx', fund.Code))
    info_str = driver.find_element_by_id("jztable").text + ' '
    driver.get(web_dict['基金基本概况']['web'].replace('xxxxxx', fund.Code))
    info_str += driver.find_element_by_class_name("txt_in").text + ' '
    dict_info = cleaning_fund_base_info(info_str)
    fund.Detail.update(dict_info)


def main_process(file_arg, logger):
    chrome_args = ['--no-sandbox', '--disable-dev-shm-usage', '--headless']
    driver = spider_init(*chrome_args)
    
    ''' Test Code
    #code = '161725'
    #code = '161028'
    title_list = [base_list_name[8], base_list_name[9],base_list_name[10], 
                    base_list_name[11], base_list_name[12]]
    list_tmp = [
        ('2020-04-24', '1.2345', '2.3456', '1.12%', 'Not Ready'),
        ('2020-05-26', '1.1111', '2.2222', '3.33%', 'Not Ready'),
    ]
    mydb = ml.mysql_client(host="182.61.47.202",user="root")
    mydb.select_db('Fund')
    mydb.insert('NetOf_161725', title_list, list_tmp, True)
    '''

    fund = FundBase(Code = file_arg)
    fund_get_info(driver, fund)
    logger.info('Fund[%s] Start Get Info...'%(file_arg))
    mydb = ml.mysql_client(host="182.61.47.202",user="root")
    logger.info('Fund[%s] Connecting to Database...'%(file_arg))
    fund_update_base_info(mydb, fund)
    logger.info('Fund[%s] Update Base Info...'%(file_arg))
    fund_update_net_info(mydb, fund)
    logger.info('Fund[%s] Update Net Info...'%(file_arg))
    #'''

    mydb.flush()
    driver.quit()
    logger.info('Fund[%s] Update Success...'%(file_arg))


if __name__ == '__main__':
    file_argv = sys.argv
    del file_argv[0]
    if len(file_argv) != 1:
        print ('argv error')
        exit()
    main_process(file_argv[0])









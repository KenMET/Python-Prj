import time
import datetime
import sys
import gc
import copy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

sys.path.append(r'../mysql/')
import mysql_lib as ml

class FundBase:
    def __init__(self, Name=None, 
                    Code=None, 
                    Detail = {
                        '成立日期':'None',
                        '最新规模':'None',
                        '基金类型':'None',
                        '管理人':'None',
                        '累计单位净值':'None',
                        '近1月':'None',
                        '近3月':'None',
                        '近6月':'None',
                        '近1年':'None',
                        '成立来':'None',
                        '净值详细数据':{
                            '1970/01/01/四': {
                                '涨跌幅':'None',
                                '单位净值':'None',
                                '净值估算':'None',
                                '09:30': {
                                    '估值':'None',
                                    '均值':'None',
                                    '跌涨幅':'None',
                                },
                            }
                        }
                    }):
        self.Name = Name
        self.Code = Code
        del Detail['净值详细数据']
        Detail.update({'净值详细数据':{}})
        self.Detail = Detail


def AC_execute(driver, elem, offset_x, offset_y):
    action = ActionChains(driver)
    action.move_to_element_with_offset(elem, offset_x, offset_y) 
    action.perform()


def spider_init(*args):
    chrome_options=Options()
    for index in args:
        chrome_options.add_argument(index)
    return webdriver.Chrome(chrome_options=chrome_options)

def fund_get_code_by_name(name):
    return None

def fund_get_dict_of_str(tmp):
    if tmp.find('估') < 0 or tmp.find('幅') < 0:
        return {}
    date = tmp[:tmp.find(':')-2]
    time = tmp[tmp.find(':')-2:tmp.find(' 估:')]
    reckon_value = float(tmp[tmp.find('估:')+2:tmp.find(' 均:')])
    avg_value = float(tmp[tmp.find('均:')+2:tmp.find(' 幅:')])
    amplitude = float(tmp[tmp.find('幅:')+2:tmp.find('%')])
    return date, {time : {'估值':reckon_value, '均值':avg_value, '跌涨幅':amplitude,}}
    
def fund_push_to_database(fund_list):
    for fund_index in fund_list:
        base_dict = fund_index.Detail
        total_db = {'名字':fund_index.Name, '代号':fund_index.Code,
                    '成立日期':'','最新规模':'','基金类型':'',
                    '管理人':'','累计单位净值':'','近1月':'',
                    '近3月':'','近6月':'','近1年':'','成立来':'',}
        mydb = ml.mysql_client(host="182.61.47.202",user="root")
        #mydb.delet_db('Fund')
        #mydb.creat_db('Fund')
        mydb.select_db('Fund')
        mydb.creat_tb('Head_Table', total_db)
        title_list = []
        list_tmp = []
        for index in total_db:
            title_list.append(index)
            list_tmp.append(base_dict.get(index, total_db[index]))
        mydb.insert_or_update('Head_Table', title_list, list_tmp, ['代号'], True)
        
        detail_in_day = fund_index.Detail['净值详细数据']
        total_db_second = {'时间':'','估值':'','均值':'','跌涨幅':'',}
        #mydb.delet_tb('Code'+fund_index.Code)
        mydb.creat_tb('Code'+fund_index.Code, total_db_second)
        title_list.clear()
        list_tmp.clear()
        for title_index in total_db_second:
            title_list.append(title_index)
        for this_day in detail_in_day:
            detail_this_day = detail_in_day[this_day]
            for detail_index in detail_this_day:
                if detail_index.find(':') >= 0:
                    val_detail = detail_this_day[detail_index]
                    list_tmp.append(this_day + ' ' + detail_index)
                    for val_index in val_detail:
                        list_tmp.append(val_detail.get(val_index, total_db_second[val_index]))
                    mydb.insert_or_update('Code'+fund_index.Code,title_list,list_tmp,['时间'],False)
                list_tmp.clear()
    mydb.flush()



def fund_info_wash(info_str):
    import re
    dict_info = {}
    dict_detail = {}
    data = re.split(r"['\n','：','|',' ']", info_str)
    while '' in data:
        data.remove('')

    dict_detail.update({'净值估算':data[2]})
    dict_detail.update({'跌涨幅':str([data[3],data[4],])})
    dict_detail.update({'单位净值':data[11]})

    dict_info.update({'近1月':data[6]})
    dict_info.update({'近3月':data[13]})
    dict_info.update({'近6月':data[19]})
    dict_info.update({'近1年':data[8]})
    dict_info.update({'成立来':data[21]})
    dict_info.update({'基金类型':str([data[23], data[24],]).replace("'",'')})
    dict_info.update({'最新规模':data[26]})
    dict_info.update({'成立日期':data[32]})
    dict_info.update({'管理人':data[36]})
    dict_info.update({'累计单位净值':data[17]})

    return dict_info, dict_detail


def fund_get_detail(driver, fund):
    if fund.Name == None and fund.Code == None:
        return {}
    if fund.Name != None and fund.Code == None:
        fund.Code = fund_get_code_by_name(fund.Name)
    if fund.Code == None:
        return {}

    driver.get('http://fund.eastmoney.com/%s.html?spm=search'%(fund.Code))
    dict_info, detail = fund_info_wash(driver.find_element_by_class_name("fundInfoItem").text)
    fund.Detail.update(dict_info)
    name = driver.find_element_by_class_name("fundDetail-tit").text
    fund.Name = name[:name.find('(')]
    print ("[%s] Get Fund Detail"%(fund.Code))
    
    driver.get('http://finance.sina.com.cn/fund/quotes/%s/bc.shtml'%(fund.Code))
    elem_base = driver.find_element_by_id("hq_chart_panel")
    fund_data = driver.find_element_by_id("fundChartCurInfo")

    height = elem_base.size['height']//2
    width = elem_base.size['width']
    last_data = ''
    same_cnt = 0
    for i in range(28, width):
        AC_execute(driver, elem_base, i * 2, height)
        reach_data = fund_data.text
        if reach_data != last_data:
            same_cnt = 0
            date, time_detail_dict = fund_get_dict_of_str(reach_data)
            if last_data == '':
                fund.Detail['净值详细数据'].update({date:{}})
            fund.Detail['净值详细数据'][date].update(time_detail_dict)
            
            last_data = reach_data
            if reach_data.find('15:00') > 0:
                break
        else:
            same_cnt += 1
            if same_cnt > 3:
                break
    fund.Detail['净值详细数据'][date].update(detail)
    print ("[%s] Get Fund hq_chart_panel"%(fund.Code))
    

def main():
    args = ['--no-sandbox', '--disable-dev-shm-usage', '--headless']
    driver = spider_init(*args)

    code_list = ['161725', '161028']

    for code_index in code_list:
        fund = FundBase(Code = code_index)
        fund_get_detail(driver, fund)
        fund_push_to_database([fund, ])
    
    driver.close()

if __name__ == '__main__':
    main()


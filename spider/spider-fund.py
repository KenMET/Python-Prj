import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

panel_pos_list = []


class FundBase:
    def __init__(self, Name=None, 
                    Code=None, 
                    Detail = {
                        '成立日期':'1970年01月01日',
                        '最新规模':'1亿',
                        '累计单位净值':0.9710,
                        '单位净值':0.9740,
                        '涨跌幅':-0.001,
                        '净值详细数据':{
                            '1970/01/01/四': {
                                '09:30': {
                                    '估值':0.9792, 
                                    '均值':0.9793, 
                                    '跌涨幅':0.0101,
                                }
                            }
                        }
                    }):
        self.Name = Name
        self.Code = Code
        del Detail['净值详细数据']['1970/01/01/四']
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
    
def fund_push_to_database(fund):
    print ('%s'%(fund.Detail['净值详细数据']))

def fund_get_detail(driver, fund):
    if fund.Name == None and fund.Code == None:
        return {}
    if fund.Name != None and fund.Code == None:
        fund.Code = fund_get_code_by_name(fund.Name)
    if fund.Code == None:
        return {}

    driver.get('http://finance.sina.com.cn/fund/quotes/%s/bc.shtml'%(fund.Code))
    elem_base = driver.find_element_by_id("hq_chart_panel")
    fund_data = driver.find_element_by_id("fundChartCurInfo")

    print (driver.find_element_by_class_name("fund_info_blk2").text)
    print (driver.find_element_by_class_name("fund_info_blk3").text)
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
    fund_push_to_database(fund)

def main():
    args = ['--no-sandbox', '--disable-dev-shm-usage', '--headless']
    driver = spider_init(*args)
    
    fund = FundBase(Code = '161725')
    fund_get_detail(driver, fund)

    driver.close()

if __name__ == '__main__':
    main()


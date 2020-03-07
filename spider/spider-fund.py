import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains



class FundBase:
    
    def __init__(self, Name=None, 
                    Code=None, 
                    Detail = {
                        '成立日期':'1970年01月01日'
                        '最新规模':'1亿'
                        '累计单位净值':0.9710,
                        '单位净值':0.9740,
                        '涨跌幅':-0.001,
                        '净值详细数据':{
                            '1970/01/01/四': {
                                '09:30': {
                                    '估值':0.9792, 
                                    '均值':0.9793, 
                                    '幅度':0.0101,
                                }
                            }
                        }
                    }):
        self.Name = Name
        self.Code = Code
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




def main():
    args = ['--no-sandbox', '--disable-dev-shm-usage', '--headless']
    driver = spider_init(*args)
    driver.get("http://finance.sina.com.cn/fund/quotes/161725/bc.shtml")


    elem_base = driver.find_element_by_id("hq_chart_panel")
    fund_data = driver.find_element_by_id("fundChartCurInfo")
    height = elem_base.size['height']//2
    width = elem_base.size['width']
    last_data = ''
    start_x = 27
    for i in range(start_x, width):
        AC_execute(driver, elem_base, i * 2, height)
        reach_data = fund_data.text
        if reach_data != last_data and not(start_x + 10 > i and reach_data.find('15:00') > 0):
            print ('[%d:%d - > %s]'%(i * 2, height, reach_data))
            last_data = reach_data
            if reach_data.find('15:00') > 0:
                break


    driver.close()

if __name__ == '__main__':
    main()


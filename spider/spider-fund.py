import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


def AC_execute(driver, elem_base, i, height):
    action = ActionChains(driver)
    action.move_to_element_with_offset(elem_base, i, height) 
    action.perform()


def main():
    chrome_options=Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')
    
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get("http://finance.sina.com.cn/fund/quotes/161725/bc.shtml")
    
    
    
    elem_base = driver.find_element_by_id("hq_chart_panel")
    fund_data = driver.find_element_by_id("fundChartCurInfo")
    height = elem_base.size['height']//2
    width = elem_base.size['width']
    last_data = ''
    for i in range(25, width):
        AC_execute(driver, elem_base, i * 2, height)
        reach_data = fund_data.text
        if (reach_data != last_data):
            print ('[%d:%d - > %s]'%(i * 2, height, reach_data))
            last_data = reach_data
        if reach_data.find('14:59') > 0:
            break


    driver.close()

if __name__ == '__main__':
    main()


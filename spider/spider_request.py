import os, sys
import time, datetime
import json
import requests

from bs4 import BeautifulSoup

py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../common_api/xml_operator'%(py_dir))
import xml_operator as xo


#all fund base data must return as a dict
def request_base(code):
    url1 = 'http://fundf10.eastmoney.com/jbgk_%s.html'%(code)

    header = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
              'Accept-Encoding': 'gzip, deflate',
              'Accept-Language': 'zh-CN,zh;q=0.9',
              'Connection': 'keep-alive',
              'Host': 'fundf10.eastmoney.com',
              'Referer': 'http://fund.eastmoney.com/',
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/86.0.4240.198 Safari/537.36',}

    response = requests.get(url=url1, headers=header)
    response.encoding = 'utf-8'
    if (response.status_code != 200):
        print ('Request Base error:[%d]'%(response.status_code))
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    main_div = soup.find('div', class_ = 'txt_cont')
    table = main_div.find_all('th')
    dup_child_dict = {}
    temp_dict = {}
    for key_index in table:
        val_index = key_index.next_sibling
        key = key_index.text
        val = ''
        internal_children = val_index.find_all(['th', 'td'])
        if (len(internal_children) > 0):
            dup_child_dict.update({key:val_index})
        else:
            val = val_index.text
        temp_dict.update({key:val})

    for key in dup_child_dict:
        internal_children = dup_child_dict[key].find_all(['th', 'td'])
        for tmp in internal_children:
            tmp.clear()
        val = dup_child_dict[key].text
        temp_dict.update({key:val})
    ####################################################
    main_div = soup.find_all('div', class_ = 'boxitem w790')
    for index in main_div:
        key_index = index.find('label', class_ = 'left')
        val_index = index.find('p')
        if (type(val_index) == type(None) or type(key_index) == type(None)):
            continue
        key = key_index.text
        val = val_index.text.replace(' ', '').replace('\r','').replace('\n','').strip()
        temp_dict.update({key:val})

    return transfer_base_to_mysql(temp_dict)

#all fund daily data must return as a dict
def request_daily(code):
    url1 = 'http://fund.eastmoney.com/%s.html'%(code)

    header = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
              'Accept-Encoding': 'gzip, deflate',
              'Accept-Language': 'zh-CN,zh;q=0.9',
              'Cache-Control': 'max-age=0',
              'Connection': 'keep-alive',
              'Host': 'fund.eastmoney.com',
              'Referer': url1,
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/86.0.4240.198 Safari/537.36',}

    response = requests.get(url=url1, headers=header)
    response.encoding = 'utf-8'
    if (response.status_code != 200):
        print ('Request Daily error:[%d]'%(response.status_code))
        return {}

    temp_dict = {}
    soup = BeautifulSoup(response.text, 'html.parser')
    main_div = soup.find('div', class_ = 'fundDetail-main')

    dateItem = main_div.find_all('dd', class_ = "dataNums")
    for index in dateItem:
        title = index.previous_sibling.find('span', class_ = 'sp01').text
        temp_dict.update({title: index.text})

    redItem = main_div.find_all('span', class_ = "ui-font-middle ui-color-red ui-num")
    for index in redItem:
        title = index.previous_sibling.text.replace('：', '')
        temp_dict.update({title: index.text})
    greenItem = main_div.find_all('span', class_ = "ui-font-middle ui-color-green ui-num")
    for index in greenItem:
        title = index.previous_sibling.text.replace('：', '')
        temp_dict.update({title: index.text})

    temp_dict.update({'ID':code})
    return transfer_daily_to_mysql(temp_dict)

#all fund net data must return as a list
def request_net(code, days):
    url1 = 'http://api.fund.eastmoney.com/f10/lsjz?callback=jQuery18308926516764027739_1607151282970&fundCode=%s&pageIndex=1&pageSize=%s&startDate=&endDate=&_=xxxxxx'%(code,days)
    url2 = url1.replace('xxxxxx', str(int(round(time.time() * 1000))))

    header = {'Accept': '*/*',
              'Accept-Encoding': 'gzip, deflate',
              'Accept-Language': 'zh-CN,zh;q=0.9',
              'Connection': 'keep-alive',
              'Host': 'api.fund.eastmoney.com',
              'Referer': 'http://fundf10.eastmoney.com/',
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/86.0.4240.198 Safari/537.36',}
    response = requests.get(url=url2, headers=header)
    response.encoding = 'utf-8'
    if (response.status_code != 200):
        print ('Request Net error:[%d]'%(response.status_code))
        return []
    data_full = response.text
    data_json = data_full[data_full.find('(')+1 : data_full.rfind(')')]  # remove head, the rest is the json data
    data_dict = json.loads(data_json)
    data_fund = data_dict['Data']
    data_list = data_fund['LSJZList']
    temp_list = []
    for index in data_list:
        temp_list.append(transfer_net_to_mysql(index))
    return temp_list


def transfer_base_to_mysql(rq_dict):
        map_dict = {
            '基金简称':'Name',
            '基金代码':'ID',
            '基金类型':'Type',
            '发行日期':'PublishDate',
            '成立日期/规模':'EstablishmentDate_Size',
            '资产规模':'AssetSize',
            '份额规模':'ShareSize',
            '基金管理人':'Manager',
            '基金托管人':'Custodian',
            '基金经理人':'ManagerPerson',
            '成立来分红':'EstablishmentDividend',
            '管理费率':'ManagementFeeRate',
            '托管费率':'HostingFees',
            '销售服务费率':'SalesServiceRate',
            '最高认购费率':'MaximumSubscriptionRate',
            '最高申购费率':'MaximumApplyRate',
            '最高赎回费率':'MaximumRedemptionRate',
            '业绩比较基准':'PerformanceComparisonBase',
            '跟踪标的':'TargetTrack',
            '投资目标':'InvestmentObjectives',
            '投资理念':'InvestmentPhilosophy',
            '投资范围':'InvestmentScope',
            '投资策略':'InvestmentStrategy',
            '分红政策':'DividendPolicy',
            '风险收益特征':'RiskReturnCharacteristics',
        }
        temp_dict = {'Reserve':''}
        for key in map_dict:
            temp_dict.update({map_dict[key]:rq_dict.get(key, '')})
        return temp_dict

def transfer_daily_to_mysql(rq_dict):
        map_dict = {
            'ID':'ID',
            '净值估算': 'NetValueCurrent', 
            '单位净值': 'NetValueUnit', 
            '累计净值': 'NetValueCumulative', 
            '近1月': 'Recent1MonthGrowth', 
            '近3月': 'Recent3MonthGrowth', 
            '近6月': 'Recent6MonthGrowth', 
            '近1年': 'Recent1YearGrowth',
            '近3年': 'Recent3YearGrowth',
            '成立来': 'SinceEstablishGrowth',
        }
        temp_dict = {'Reserve':''}
        for key in map_dict:
            temp_dict.update({map_dict[key]:rq_dict.get(key, '')})
        NetValueUnit = temp_dict['NetValueUnit'][:temp_dict['NetValueUnit'].find('.')+5]
        NetValueUnitGrowth = temp_dict['NetValueUnit'][temp_dict['NetValueUnit'].find('.')+5:]
        temp_dict.update({'NetValueUnit':NetValueUnit})
        temp_dict.update({'NetValueUnitGrowth':NetValueUnitGrowth})

        return temp_dict

def transfer_net_to_mysql(rq_dict):
        map_dict = {
            'FSRQ': 'NetValueDate', 
            'DWJZ': 'NetValueUnit', 
            'LJJZ': 'NetValueCumulative', 
            'JZZZL': 'DayGrowth', 
            'SGZT': 'SubscriptionStatus', 
            'SHZT': 'RedemptionStatus', 
            'FHSP': 'DividendsSending',
        }
        temp_dict = {'Reserve':''}
        for key in map_dict:
            temp_dict.update({map_dict[key]:rq_dict.get(key, '')})
        return temp_dict

if __name__ == '__main__':
    #print (request_net('001593', 2))
    #temp = request_base('161028')
    #for index in temp:
    #    print ('[%s]:%s'%(index, temp[index]))
    temp = request_daily('161028')
    print (temp)
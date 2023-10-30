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
def request_cat_survey(code):
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
def request_daily_growth(code):
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

    temp_dict = {}
    soup = BeautifulSoup(response.text, 'html.parser')
    main_div = soup.find('div', class_ = 'col-right')
    p = main_div.find('p', class_ = 'row row1')
    labels = p.find_all('label')
    for index in labels:
        temp = index.text.replace(' ', '').replace('\r','').replace('\n','')
        title = temp[:temp.find('：')]
        if title.find('（') >= 0:
            title_front = title[:title.find('（')]
            title_rear = title[title.find('）')+len('）'):]
            title = title_front + title_rear
        value = temp[temp.find('：')+len('：'):]
        temp_dict.update({title:value})

    temp_dict.update({'ID':code})
    return transfer_daily_to_mysql(temp_dict)

#all fund net data must return as a list
def request_net_history(code, days):
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

def request_holdings(code, year):
    url1 = 'http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code=%s&topline=100&year=%s&month=3&rt=0.8030068316922307'%(code, year)
    header = {'Accept': '*/*',
              'Accept-Encoding': 'gzip, deflate',
              'Accept-Language': 'zh-CN,zh;q=0.9',
              'Connection': 'keep-alive',
              'Host': 'fundf10.eastmoney.com',
              'Referer': 'http://fundf10.eastmoney.com/ccmx_%s.html'%(code),
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/86.0.4240.198 Safari/537.36',}
    response = requests.get(url=url1, headers=header)
    response.encoding = 'utf-8'
    if (response.status_code != 200):
        print ('Request Net error:[%d]'%(response.status_code))
        return []
    data_full = response.text
    data_json = data_full.replace('var apidata={ content:"', '').replace('', '')
    data_json = data_json[:data_json.rfind('",arryear')]
    soup = BeautifulSoup(data_json, 'html.parser')
    form_list = soup.find_all('table')
    range_list = soup.find_all('h4')
    if len(form_list) != len(range_list):
        print ('Not match[%d : %d]'%(len(form_list), len(range_list)))
        return {}
    holdings_list = []
    for form_index in form_list:
        range_index = range_list[form_list.index(form_index)]
        range_date = range_index.find('font').text
        item_list = form_index.find_all('tr')
        for item_index in item_list:
            temp_dict = {}
            a_list = item_index.find_all('a')
            for a_index in a_list:
                parent_class = a_index.parent.attrs.get('class')
                if parent_class == ['tol']:
                    temp_dict.update({'DogName':a_index.text.replace('\r','').replace('\n','').replace(' ','')})
                elif parent_class == None:
                    temp_dict.update({'DogCodeQuarter':range_date + ':' + a_index.text.replace('\r','').replace('\n','').replace(' ','')})
            td_first = item_index.find('td', class_ = 'tor')
            if td_first == None:
                continue
            while td_first.find('span') != None or td_first.find('a') != None:
                td_first = td_first.next_sibling
            temp_dict.update({'DogProportion':td_first.text.replace('\r','').replace('\n','').replace(' ','')})
            next_bro = td_first.next_sibling
            temp_dict.update({'DogShare':next_bro.text.replace('\r','').replace('\n','').replace(' ','')})
            next_bro = next_bro.next_sibling
            temp_dict.update({'DogMarketValue':next_bro.text.replace('\r','').replace('\n','').replace(' ','')})
            if (len(temp_dict) > 0):
                holdings_list.append(temp_dict)
    return holdings_list

'''
https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?cb=jQuery1123013525801697988382_1661079347262& lmt=0&klt=101&fields1=f1%2Cf2%2Cf3%2Cf7&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf62%2Cf63%2Cf64%2Cf65&ut=b2884a393a59ad64002292a3e90d46a5&secid=0.002074&_=1661079347263
https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?cb=jQuery11230018430337025947985_1661084285964&lmt=0&klt=101&fields1=f1%2Cf2%2Cf3%2Cf7&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf62%2Cf63%2Cf64%2Cf65&ut=b2884a393a59ad64002292a3e90d46a5&secid=1.600036&_=1661084285965
https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?cb=jQuery112306277901112223307_1661092252881&  lmt=0&klt=101&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65&ut=b2884a393a59ad64002292a3e90d46a5&secid=0.002074&_=1661092252882
https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?cb=jQuery112301932308102447975_1663597850322&  lmt=0&klt=101&fields1=f1%2Cf2%2Cf3%2Cf7&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf62%2Cf63%2Cf64%2Cf65&ut=b2884a393a59ad64002292a3e90d46a5&secid=1.600066&_=1663597850323
'''
def request_dog_money_flows(code):
    url1 = 'https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65&secid=0.%s&_=%d'%(code, int(time.time() * 1000))
    header = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
              'Accept-Encoding': 'gzip, deflate',
              'Accept-Language': 'zh-CN,zh;q=0.9',
              'Connection': 'keep-alive',
              'Host': 'push2his.eastmoney.com',
              'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
              'sec-ch-ua-mobile': '?0',
              'sec-ch-ua-platform': '"Windows"',
              'Sec-Fetch-Dest': 'document',
              'Sec-Fetch-Mode': 'navigate',
              'Sec-Fetch-Site': 'none',
              'Sec-Fetch-User': '?1',
              'Upgrade-Insecure-Requests': '1',
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/86.0.4240.198 Safari/537.36',}
    response = requests.get(url=url1, headers=header)
    response.encoding = 'utf-8'
    if (response.status_code != 200):
        print ('Request Net error:[%d]'%(response.status_code))
        return []
    main_data = json.loads(response.text).get('data')
    if main_data == None:
        time.sleep(5)
        response = requests.get(url=url1.replace('secid=0', 'secid=1'), headers=header)
        response.encoding = 'utf-8'
        if (response.status_code != 200):
            print ('Request Net error:[%d]'%(response.status_code))
            return []
        main_data = json.loads(response.text).get('data')
        if main_data == None:
            return []
    temp_list = []
    if main_data.get('code', '') != code:
        return temp_list
    klines_list = main_data.get('klines', [])
    for index in klines_list:
        if type(index) == type('String'):
            item_list = index.split(',')
            temp_dict = {
                'Date': item_list[0],
                'MainIn': item_list[1],
                'LittleIn': item_list[2],
                'MiddIn': item_list[3],
                'BigIn': item_list[4],
                'BigPlusIn': item_list[5],
                'MainPer': item_list[6],
                'LittlePer': item_list[7],
                'MiddPer': item_list[8],
                'BigPer': item_list[9],
                'BigPlusPer': item_list[10],
                'CloseValue': item_list[11],
                'CloseRate': item_list[12],
            }
            temp_list.append(temp_dict)
    return temp_list

def request_top_news(count):
    request_count = (count // 40) + 1
    temp_list = []
    for i in range(request_count):
        url1 = 'https://roll.eastmoney.com/list?count=40&type=&pageindex=%d'%(i + 1)
        header = {'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Host': 'roll.eastmoney.com',
                'Referer': 'https://roll.eastmoney.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/86.0.4240.198 Safari/537.36',}
        response = requests.get(url=url1, headers=header)
        response.encoding = 'utf-8'
        if (response.status_code != 200):
            print ('Request Net error:[%d]'%(response.status_code))
            return []
        news_list = json.loads(response.text)
        for index in news_list:
            temp_list.append(transfer_news_to_mysql(index))
        time.sleep(2)
    return temp_list

def request_top_news_content(url):
    if (url.find('stock.eastmoney.com') >= 0 or url.find('futures.eastmoney.com') >= 0):
        url = url.replace('stock.eastmoney.com', 'finance.eastmoney.com')
        url = url.replace('futures.eastmoney.com', 'finance.eastmoney.com')
    if (url.find('fund.eastmoney.com') >= 0):
        url = url.replace('http://', 'https://')
    header = {'Accept': 'text/html',
              'Accept-Encoding': 'gzip, deflate',
              'Accept-Language': 'zh-CN,zh;q=0.9',
              'Connection': 'keep-alive',
              'Host': 'finance.eastmoney.com',
              #'Host': url[:url.find('.com')+4].replace('http://', ''),
              #'Referer': 'https://roll.eastmoney.com/',
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/86.0.4240.198 Safari/537.36',}
    response = requests.get(url=url, headers=header)
    response.encoding = 'utf-8'
    if (response.status_code != 200):
        print ('Request http failed[%s] error:[%d], retry https'%(url, response.status_code))
        url = url.replace('http://', 'https://')
        response = requests.get(url=url, headers=header)
        response.encoding = 'utf-8'
        if (response.status_code != 200): 
            print ('Request https still failed[%s] error:[%d]'%(url, response.status_code))
            return ""

    soup = BeautifulSoup(response.text, 'html.parser')
    content_div = soup.find('div', {"id":'ContentBody'})
    p = content_div.find_all('p')
    content = ""
    for p_index in p:
        line_str = p_index.get_text()
        if (line_str == None or len(line_str.strip()) == 0):
            continue
        content += line_str.strip() + '; '

    if (len(content.strip()) == 0):
        #print ('using content_div.text')
        return content_div.text.strip()

    return content

def request_cat_news(code):
    temp_list = []

    return temp_list

def request_dog_news(code):
    temp_list = []

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
        #'净值估算': 'NetValueCurrent',
        '盘中估算': 'NetValueCurrent',
        '单位净值': 'NetValueUnit', 
        #'累计净值': 'NetValueCumulative', 
        #'近1月': 'Recent1MonthGrowth', 
        #'近3月': 'Recent3MonthGrowth', 
        #'近6月': 'Recent6MonthGrowth', 
        #'近1年': 'Recent1YearGrowth',
        #'近3年': 'Recent3YearGrowth',
        #'成立来': 'SinceEstablishGrowth',
    }
    temp_dict = {'Reserve':''}
    for key in map_dict:
        temp_dict.update({map_dict[key]:rq_dict.get(key, '')})
    NetValueCurrent = temp_dict['NetValueCurrent'][:temp_dict['NetValueCurrent'].find('.')+5]
    NetValueCurrentGrowth = temp_dict['NetValueCurrent'][temp_dict['NetValueCurrent'].find('.')+5:]
    temp_dict.update({'NetValueCurrent':NetValueCurrent})
    temp_dict.update({'NetValueCurrentGrowth':NetValueCurrentGrowth})

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

def transfer_news_to_mysql(rq_dict):
    map_dict = {
        'title': 'Title', 
        'type': 'Type', 
        'time': 'Time', 
        'url': 'Url', 
        'channelUrl': 'ChannelUrl', 
    }
    temp_dict = {'Reserve':''}
    for key in map_dict:
        temp_dict.update({map_dict[key]:rq_dict.get(key, '')})
    return temp_dict

if __name__ == '__main__':
    #print (request_net_history('001593', 2))
    #temp = request_cat_survey('161028')
    #for index in temp:
    #    print ('[%s]:%s'%(index, temp[index]))
    #temp = request_daily2('161028')
    #print (temp)
    #temp = request_holdings('161028', '2023')
    #print (temp)
    temp = request_dog_money_flows('600066')
    print (temp)


import time
import datetime
import json
import requests
from bs4 import BeautifulSoup

#all fund base data must return as a list
def request_base(code):
    url1 = 'http://fundf10.eastmoney.com/jjjz_%s.html'%(code)
    print (url1)

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
    data_full = response.text
    
    base_dict = {'单位净值':'1.000', 
                '涨幅':'0.00%',
                '交易状态':{'buy':True,'sell':True},
                '买入费率':'0.10%',}
    
    current_net = data_full[data_full.find('单位净值'):]
    current_net = current_net[:current_net.find('</label>')]
    NVA_PER = current_net[current_net.find('<b class="grn lar bold">')+len('<b class="grn lar bold">'):current_net.find('</b>')]
    NVA = NVA_PER[:NVA_PER.find('(')]
    PER = NVA_PER[NVA_PER.find('(')+1:NVA_PER.find(')')]
    base_dict['单位净值'] = NVA
    base_dict['涨幅'] = PER

    fund_state = data_full[data_full.find('交易状态'):]
    fund_state = fund_state[:fund_state.find('</label>')]
    buy_state = fund_state[fund_state.find('<span>'):fund_state.find('</span>')]
    sell_state = fund_state[fund_state.rfind('<span>'):fund_state.rfind('</span>')]
    if buy_state.find('暂停') >= 0:
        base_dict['交易状态']['buy'] = False
    if sell_state.find('暂停') >= 0:
        base_dict['交易状态']['sell'] = False

    sourcerate = data_full[data_full.find('<b class="sourcerate">'):]
    sourcerate = sourcerate[:sourcerate.find('</label>')]
    sourcerate = sourcerate[sourcerate.find('<b>'):]
    buy_rate = sourcerate[sourcerate.find('<b>')+3:sourcerate.find('</b>')]
    base_dict['买入费率'] = buy_rate

    for index in base_dict:
        if type('string') == type(base_dict[index]):
            base_dict[index] = base_dict[index].replace('\r','').replace('\n','').strip().rstrip()

    #print(current_net)
    #print(fund_state)
    #print(sourcerate)
    print(base_dict)
    return base_dict

#all fund net data must return as a list
def request_net_clean(code, days):
    url1 = 'http://api.fund.eastmoney.com/f10/lsjz?callback=jQuery18308926516764027739_1607151282970&fundCode=%s&pageIndex=1&pageSize=%s&startDate=&endDate=&_=xxxxxx'%(code,days)
    url2 = url1.replace('xxxxxx', str(int(round(time.time() * 1000))))
    print (url2)

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
    data_full = response.text
    data_json = data_full[data_full.find('(')+1 : data_full.find(')')]  #去掉头，剩下就是json格式数据
    data_dict = json.loads(data_json)
    data_fund = data_dict['Data']
    data_list = data_fund['LSJZList']
    return data_list

def main():
    #list = request_base_clean('161725')
    #for index in list:
    #    print (index)

    request_base('161725')


if __name__ == '__main__':
    main()

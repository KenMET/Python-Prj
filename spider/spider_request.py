import time
import datetime
import json
import requests
from bs4 import BeautifulSoup

#all fund base data must return as a list
def request_base_clean(code):
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

    soup = BeautifulSoup(response.text, features="html.parser")
    print (soup.find_all ( "div" , class_ = "basic-new" ))
    
    return []

#all fund net data must return as a list
def request_net_clean(code):
    url1 = 'http://api.fund.eastmoney.com/f10/lsjz?callback=jQuery18308926516764027739_1607151282970&fundCode=%s&pageIndex=1&pageSize=20&startDate=&endDate=&_=xxxxxx'%(code)
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
    list = request_net_clean('161725')
    for index in list:
        print (index)

if __name__ == '__main__':
    main()

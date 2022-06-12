import time
import datetime
import json
import requests

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

    base_dict = {
                'Id':code,
                'Name':'None',
                'Date':'',
                'NetValue':'1.000', 
                'Amplitude':'0.00%',
                'BuyStatus':True,
                'SellStatus':True,
                'BuyRate':'0.10%',}

    find_str = '<h4 class="title"><a href="http://fund.eastmoney.com/%s.html">'%(code)
    name = data_full[data_full.find(find_str)+len(find_str):]
    name = name[:name.find('</h4>')]
    name = name[:name.find(' ')]
    base_dict['Name'] = name
    
    current_net = data_full[data_full.find('盘中估算'):]
    current_net = current_net[:current_net.find('</label>')]
    find_str = '<span id="fund_gsz"'
    NVA = current_net[current_net.find(find_str)+len(find_str):]
    NVA = NVA[NVA.find('>')+1:]
    NVA = NVA[:NVA.find('</span>')]
    find_str = '<span id="fund_gszf"'
    PER = current_net[current_net.find(find_str)+len(find_str):]
    PER = PER[PER.find('>')+1:]
    PER = PER[:PER.find('</span>')]
    base_dict['NetValue'] = NVA
    base_dict['Amplitude'] = PER

    find_str = '单位净值（'
    date = data_full[data_full.find(find_str)+len(find_str):]
    date = date[:date.find('）：')]
    base_dict['Date'] = str(datetime.datetime.now().year) + '-' + date

    fund_state = data_full[data_full.find('交易状态'):]
    fund_state = fund_state[:fund_state.find('</label>')]
    buy_state = fund_state[fund_state.find('<span>'):fund_state.find('</span>')]
    sell_state = fund_state[fund_state.rfind('<span>'):fund_state.rfind('</span>')]
    if buy_state.find('暂停') >= 0:
        base_dict['BuyStatus'] = False
    if sell_state.find('暂停') >= 0:
        base_dict['SellStatus'] = False

    sourcerate = data_full[data_full.find('<b class="sourcerate">'):]
    sourcerate = sourcerate[:sourcerate.find('</label>')]
    sourcerate = sourcerate[sourcerate.find('<b>'):]
    buy_rate = sourcerate[sourcerate.find('<b>')+3:sourcerate.find('</b>')]
    base_dict['BuyRate'] = buy_rate

    for index in base_dict:
        if type('string') == type(base_dict[index]):
            base_dict[index] = base_dict[index].replace('\r','').replace('\n','').strip().rstrip()

    #print(current_net)
    #print(fund_state)
    #print(sourcerate)
    #print(base_dict)
    return base_dict

#all fund net data must return as a list
def request_net(code, days):
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
    print (request_net('001629', 8))
    print (request_base('001629'))


if __name__ == '__main__':
    main()

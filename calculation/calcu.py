import os
import sys
import time
import datetime
import threading
import multiprocessing
import json
from socket import *
import logging


mutex=threading.Lock()
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../mysql/'%(py_dir))
sys.path.append(r'%s/../spider/'%(py_dir))
sys.path.append(r'%s/../common/alphabet/'%(py_dir))
import alphabet_pro as alphabet
import spider_request as spi_req
import mysql_lib as mysql

def before_proc(data):
    for index in data:
        del index[2]
    return data[::-1]


# value formula:
#   now have the info of N-1 day, need calculat the N day info
#   val[N-1] * (1+per[N]) = val[N]
#

#daily_db = {'Id':'', 'Name':'', 'Date':'', 'NetValue':'','Amplitude':'','BuyStatus':'','SellStatus':'', 'Money':'', 'RiseSellCnt':'', 'FallBuyCnt':'', 'LastActCnt':''}
#config = {'Id':'', 'Name':'', 'StartMoney':'', 'MoneyLimit':'', 'RiseSell':'', 'SellPer':'', 'FallBuy':'', 'BuyPer':'', 'BuyRate':'',}
def simulate_calcu(data_list, rule_dict):
    rise_cnt = 0
    fall_cnt = 0
    money = round(float(rule_dict['StartMoney']), 2)
    money_pool = round(float(rule_dict['MoneyLimit']), 2) - money
    last_cnt = 0

    for data_index in (data_list):
        if data_index == []:
            continue
        if data_index[3] == '' or data_index[3] == '%':
            continue
        per = float(data_index[3].replace('%','')) / 100
        money += money * per
        if (abs(per) < 0.001):
            continue
        if (per > 0):
            rise_cnt += 1
        elif (per < 0):
            fall_cnt += 1
        
        if rise_cnt >= rule_dict['RiseSell']:
            rise_cnt = 0
            fall_cnt = 0
            sell_money = money * float(rule_dict['SellPer'])
            if last_cnt < 7:
                fee = sell_money * 0.015
                sell_money += fee
            else:
                fee = sell_money * 0.0015
                sell_money += fee
            if fee > money * per:
                continue
            money -= sell_money
            money_pool += sell_money
            #print ('[%s] money[%f] per[%f] --sell[%f(%f)]->  pool[%f]'%(data_index[0], money, per, sell_money, fee, money_pool))
            #print ('%s,%s,-1'%(data_index[0], data_index[1]))
            last_cnt = 0
        elif fall_cnt >= rule_dict['FallBuy']:
            rise_cnt = 0
            fall_cnt = 0
            buy_money = money * float(rule_dict['BuyPer'])
            fee = buy_money * 0.001
            temp = buy_money + fee
            if temp > money_pool:
                buy_money = money_pool / 1.001
                fee = buy_money * 0.001
            money += buy_money
            money_pool -= buy_money + fee
            #print ('[%s] money[%f] per[%f] <-buy[%f(%f)]--  pool[%f]'%(data_index[0], money, per, buy_money, fee, money_pool))
            #print ('%s,%s,1'%(data_index[0], data_index[1]))
            last_cnt = 0
        else:
            last_cnt += 1
            if (per > 0):
                fall_cnt = 0
            elif (per < 0):
                rise_cnt = 0
            #print ('[%s] money[%f] per[%f] ---wait---  pool[%f]'%(data_index[0], money, per, money_pool))
            #print ('%s,%s'%(data_index[0], data_index[1]))

    return (money + money_pool)


def run_simulator(data_list, base_dict, max_per):
    start_up = round(float(base_dict['MoneyLimit']), 2)

    final_tmp = simulate_calcu(data_list, base_dict)

    final_money = round(final_tmp, 2)
    rise_per = (final_money - start_up) / start_up
    rise_per_str = str(round(100 * rise_per, 2)) + '%'
    #max_per = base_dict['MaxPer']
    #if rise_per > max_per:
        #max_per = rise_per
        #print ('RiseSell[%d] SellPer[%f] FallBuy[%d] BuyPer[%f]'%(
        #        base_dict['RiseSell'], base_dict['SellPer'], 
        #        base_dict['FallBuy'], base_dict['BuyPer']))
        #print ('[%f] --> [%f] ----------> Per[%s]'%(start_up, final_money, rise_per_str))

    return [rise_per, final_money]

def connet_to_mysql():
    mydb = mysql.mysql_client(host="sdm723414637.my3w.com",user="sdm723414637", passwd="WEIyuYAN2feiNot")
    mydb.select_db('sdm723414637_db')
    return mydb

def get_net_from_mysql(mydb, code, days):
    data = mydb.show_tb('net_%s'%(code), None)
    return data[-days:]

def get_fund_daily_detail(code):
    DBlist = spi_req.request_base(code)
    return DBlist

def get_fund_history_detail(code, days):
    mydb = connet_to_mysql()
    temp = get_net_from_mysql(mydb, code, days)
    DBlist = []
    for index in temp:
        DBlist.append(list(index))
    return DBlist


#calcu_XXXXXX = {'DateRange':'', 'RiseSell':'', 'SellPer':'', 'FallBuy':'', 'BuyPer':'', 'FinalMoney':'', 'MaxPer':''}
def run_suggestion(start_money, money_limit, range_dict, data_list, calcu_list):
    base_dict = {
        'DateRange' : '',
        'StartMoney' : start_money,
        'MoneyLimit' : money_limit,
        'RiseSell' : 0,
        'SellPer' : 0.0,
        'FallBuy' : 0,
        'BuyPer' : 0.0,
        'BuyRate' : 0.0,
        'FinalMoney' : 0, 
        'MaxPer' : -100.0
    }
    final_dict = {
        'DateRange' : '',
        'StartMoney' : start_money,
        'MoneyLimit' : money_limit,
        'RiseSell' : 0,
        'SellPer' : 0.0,
        'FallBuy' : 0,
        'BuyPer' : 0.0,
        'BuyRate' : 0.0,
        'FinalMoney' : 0, 
        'MaxPer' : -100.0
    }

    for rise_sell in range(range_dict['RiseSell'][0], range_dict['RiseSell'][1]):
        for fall_buy in range(range_dict['RiseSell'][0], range_dict['RiseSell'][1]):
            for sell_per in range(range_dict['SellPer'][0], range_dict['SellPer'][1]):
                for buy_per in range(range_dict['BuyPer'][0], range_dict['BuyPer'][1]):
                    base_dict['RiseSell'] = rise_sell
                    base_dict['FallBuy'] = fall_buy
                    base_dict['SellPer'] = sell_per / 10
                    base_dict['BuyPer'] = buy_per / 10
                    tmp_list = run_simulator(data_list, base_dict, base_dict['MaxPer'])
                    base_dict['FinalMoney'] = tmp_list[1]
                    base_dict['MaxPer'] = tmp_list[0]
                    if base_dict['MaxPer'] > final_dict['MaxPer']:
                        final_dict.update(base_dict)

    final_dict['SellPer'] = str(round(final_dict['SellPer'] * 100, 2)) + '%'
    final_dict['BuyPer'] = str(round(final_dict['BuyPer'] * 100, 2)) + '%'
    final_dict['MaxPer'] = str(round(final_dict['MaxPer'] * 100, 2)) + '%'
    final_dict['DateRange'] = '%s - %s'%(data_list[0][0], data_list[-1][0])
    calcu_list.append(final_dict)

def history_detail_devide(data_list, devide_type):
    list_total = []
    start_date = data_list[0][0]
    list_total.append(list())
    count = 0
    if devide_type == 'year':
        devide_len = 4
    elif devide_type == 'month':
        devide_len = 7
    else:
        devide_len = 2
    for date_index in data_list:
        date = date_index[0]
        if start_date[:devide_len] == date[:devide_len]:
            list_total[count].append(date_index)
        else:
            list_total.append(list())
            count = count + 1
            start_date = date
            list_total[count].append(date_index)
    
    return list_total

def sort_calcu_ret(calcu_list):
    for i in range(0, len(calcu_list) - 1):
        for j in range(i, len(calcu_list)):
            year = int(calcu_list[i]['DateRange'][:4])
            year_2 = int(calcu_list[j]['DateRange'][:4])
            if year > year_2:
                calcu_list[i], calcu_list[j] = calcu_list[j], calcu_list[i]
    return calcu_list

def run(code, days, rule_dict):
    range_dict = {'RiseSell':rule_dict['RiseSell'], 'FallBuy':rule_dict['FallBuy'], 
                'SellPer':rule_dict['SellPer'], 'BuyPer':rule_dict['BuyPer']}
    start_money = int(rule_dict['StartMoney'])
    money_limit = int(rule_dict['MoneyLimit'])
    data_list = get_fund_history_detail(code, days)
    devide_list = history_detail_devide(data_list, 'year')

    mutil_jobs = []
    manager = multiprocessing.Manager()
    calcu_list = manager.list()
    for index in devide_list:
        pt = multiprocessing.Process(target=run_suggestion, args=(start_money, money_limit, range_dict, index, calcu_list))
        mutil_jobs.append(pt)
        pt.start()

    for index_job in mutil_jobs:
        index_job.join()
        
    return sort_calcu_ret(calcu_list)

#daily_db = {'Id':'', 'Name':'', 'Date':'', 'NetValue':'','Amplitude':'','BuyStatus':'','SellStatus':'', 'Money':'', 'RiseSellCnt':'', 'FallBuyCnt':'', 'LastActCnt':''}
#config = {'Id':'', 'Name':'', 'StartMoney':'', 'MoneyLimit':'', 'RiseSell':'', 'SellPer':'', 'FallBuy':'', 'BuyPer':'', 'BuyRate':'',}
def run_today(calcu_dict, config_dict, today_list):
    ret_dict = {
        'TodayExpect':'',
        'Action':'',
        'Per':'',
        'Part':'',
        'ActionMoney':'',
        'Fees':'',
    }
    rise_cnt = int(calcu_dict['RiseSellCnt'])
    fall_cnt = int(calcu_dict['FallBuyCnt'])
    money = round(float(calcu_dict['Money']), 2)
    money_pool = round(float(config_dict['MoneyLimit']), 2) - money
    last_cnt = int(calcu_dict['LastActCnt'])

    if today_list == []:
        per = 0
    elif today_list[3] == '' or today_list[3] == '%':
        per = 0
    else:
        per = float(today_list[3].replace('%','')) / 100
    ret_dict.update({'TodayExpect':str(round(money * per, 2)), 'Action':'Skip', 'Per':'', 'Part':'', 'ActionMoney':'', 'Fees':'',})
    money += money * per

    if (abs(per) < 0.001):
        ret_dict.update({'Action':'Skip->Too-Low'})
        return ret_dict
    if (per > 0):
        rise_cnt += 1
    elif (per < 0):
        fall_cnt += 1

    if rise_cnt >= int(config_dict['RiseSell']):
        sell_money = money * float(config_dict['SellPer'].replace('%','')) / 100
        if last_cnt < 7:
            fee = sell_money * 0.015
            sell_money += fee
        else:
            fee = sell_money * 0.005
            sell_money += fee
        if fee > money * per:
            ret_dict.update({'Action':'Skip->Fee-Higher-Than-Expect'})
            return ret_dict
        money -= sell_money
        money_pool += sell_money
        ret_dict.update({'Action':'Sell', 'Per':config_dict['SellPer'], 'Part':'', 'ActionMoney':str(sell_money - fee), 'Fees':str(fee)})
    elif fall_cnt >= int(config_dict['FallBuy']):
        buy_money = money * float(config_dict['BuyPer'].replace('%','')) / 100
        buy_rate = float(config_dict['BuyRate'].replace('%','')) / 100
        fee = buy_money * buy_rate
        temp = buy_money + fee
        if temp > money_pool:
            buy_money = money_pool / buy_rate
            fee = buy_money * buy_rate
        money += buy_money
        money_pool -= buy_money + fee
        ret_dict.update({'Action':'Buy', 'Per':config_dict['BuyPer'], 'Part':'', 'ActionMoney':str(buy_money), 'Fees':str(fee)})

    return ret_dict

def calcu_expect(last_money, last_date, today_amplitude, today_date, money_pool, 
                    rise_cnt, fall_cnt, rise_limit, fall_limit, 
                    buy_per, sell_per, buy_rate, sell_rate_list):
    today_expect = last_money * today_amplitude

    if (abs(today_amplitude) < 0.001):
        return today_expect, 1, 0, 0

    if (today_amplitude > 0):
        rise_cnt += 1
    elif (today_amplitude < 0):
        fall_cnt += 1

    if rise_cnt >= rise_limit:
        if last_money < 0.1:
            return today_expect, 0, 0, 0
        sell_money = last_money * sell_per
        dateq = datetime.datetime.strptime(last_date,'%Y-%m-%d').date()
        dateh = datetime.datetime.strptime(today_date,'%Y-%m-%d').date()
        datec = dateh - dateq
        if datec.days < 7:
            fee = sell_money * sell_rate_list[0]
        else:
            fee = sell_money * sell_rate_list[1]
        if fee > today_expect:
            return today_expect, 2, 0, 0
        action_money = sell_money + fee
        return today_expect, 3, -action_money, fee
    elif fall_cnt >= fall_limit:
        if last_money <= 0.1:
            action_money = 5000
        else:
            action_money = last_money * buy_per
        if (action_money + last_money) > money_pool:
            action_money = money_pool - last_money
        fee = action_money * buy_rate
        return today_expect, 4, action_money, fee
    return today_expect, 0, 0, 0

def test_run(data_list, calcu_dict):
    if len(data_list) == 0:
        return {}

    last_money = calcu_dict['Money']
    last_date = calcu_dict['LastActDate']
    rise_cnt = calcu_dict['RiseSellCnt']
    fall_cnt = calcu_dict['FallBuyCnt']
    money_pool = calcu_dict['MoneyPool']

    rise_limit = calcu_dict['RiseSell']
    fall_limit = calcu_dict['FallBuy']
    buy_per = calcu_dict['BuyPer'] / 100
    sell_per = calcu_dict['SellPer'] / 100
    buy_rate = calcu_dict['BuyRate'] / 100
    sell_rate_under7 = calcu_dict['SellRate'][0] / 100
    sell_rate_over7 = calcu_dict['SellRate'][1] / 100
    for data_index in data_list[1:]:
        temp_str = ''
        if data_index[3].find('%') > 0:
            today_amplitude = float(data_index[3].replace('%','')) / 100
        else:
            today_amplitude = 0
        today_date = data_index[0]
        today_expect, action, action_money, fee = calcu_expect(last_money, last_date, today_amplitude,
            today_date, money_pool, rise_cnt, fall_cnt, rise_limit, fall_limit, buy_per, sell_per, 
            buy_rate, [sell_rate_under7, sell_rate_over7])
        #最新值 = 上次值 + 买入值 - 手续费 + 上次值的涨跌
        last_money = last_money + (action_money - fee) + today_expect
        today_fucking_money = last_money-action_money-today_expect+fee
        tomorrow_fucking_money = last_money
        money_pool += (today_expect - fee)
        if action == 0:
            if today_amplitude > 0:
                rise_cnt = rise_cnt + 1
            else:
                fall_cnt = fall_cnt + 1
        elif action >= 3:
            rise_cnt = 0
            fall_cnt = 0
            last_date = today_date
            #temp_str = str(ret_dict['ActionMoney'])
            #print ('%s [%s] Action: %s [%f ->[%f %s]-> %f] Fee[%f] pool[%f]'%(today_date, data_index[3], ret_dict['Action'], 
            #    today_fucking_money, ret_dict['TodayExpect'], temp_str, tomorrow_fucking_money, ret_dict['Fees'], money_pool))
    return money_pool

def test_run_for_mutil_th(list_index, calcu_dict, rule_dict):
    for rise_sell in range(rule_dict['RiseSell'][0], rule_dict['RiseSell'][1]):
        for fall_buy in range(rule_dict['FallBuy'][0], rule_dict['FallBuy'][1]):
            for sell_per in range(rule_dict['SellPer'][0], rule_dict['SellPer'][1], 10):
                for buy_per in range(rule_dict['BuyPer'][0], rule_dict['BuyPer'][1], 10):
                    #ticks = time.time()
                    fund_calcu_dict = {
                        'Id':'161725', 'Name':'', 'Date':'', 'NetValue':'',
                        'Amplitude':'','BuyStatus':'','SellStatus':'', 'MoneyPool':100000.0,
                        'Money':0.0, 'RiseSellCnt':0, 'FallBuyCnt':0, 'LastActDate':list_index[0][0],
                        'RiseSell':rise_sell, 'SellPer':sell_per,
                        'FallBuy':fall_buy,  'BuyPer':buy_per,
                        'BuyRate':0.10, 'SellRate':[1.5,0.5]
                    }

                    final_money = test_run(list_index, fund_calcu_dict)
                    calcu_dict.update({final_money:fund_calcu_dict})
                    #print ('test sec [%f]'%(ticks - time.time()))

if __name__ == '__main__':
    ticks = time.time()
    '''
    rule_dict = {'StartMoney':'5000', 'MoneyLimit':'100000', 
                'RiseSell':[2,8], 'FallBuy':[2,8], 'SellPer':[1,10], 'BuyPer':[1,20]}
    calcu_list, ret_dict = run('161725', 200, rule_dict)
    print (calcu_list)
    print (ret_dict)
    '''
    max_per = -100
    data_list = get_fund_history_detail('161725', 200)
    devide_list = history_detail_devide(data_list, 'year')
    rule_dict = {'RiseSell':[2,8], 'FallBuy':[2,8], 'SellPer':[10,100], 'BuyPer':[10,200]}
    mutil_jobs = []
    manager = multiprocessing.Manager()
    calcu_dict_list = []

    cnt = 0
    for list_index in devide_list:
        calcu_dict_list.append(manager.dict())
        pt = multiprocessing.Process(target=test_run_for_mutil_th, args=(list_index, calcu_dict_list[cnt], rule_dict))
        mutil_jobs.append(pt)
        pt.start()
        cnt = cnt + 1
    for index_job in mutil_jobs:
        index_job.join()
    
    cnt = 0
    for list_index in devide_list:
        max_money = max(sorted(calcu_dict_list[cnt]))
        calcu_dict = calcu_dict_list[cnt][max_money]
        increase = ((max_money - float(calcu_dict['MoneyPool'])) / float(calcu_dict['MoneyPool'])) * 100
        str_tmp = 'From %s to %s  Final[%f -> %f] [%s%%]'%(list_index[0][0], list_index[-1][0], calcu_dict['MoneyPool'], max_money, str(round(increase,2)))
        print (str_tmp)
        print (calcu_dict)
        cnt = cnt + 1
    
    print ('using sec [%d]'%(round(time.time() - ticks)))
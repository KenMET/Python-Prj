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


def before_proc(data):
    for index in data:
        del index[2]
    return data[::-1]


# value formula:
#   now have the info of N-1 day, need calculat the N day info
#   val[N-1] * (1+per[N]) = val[N]
#


def simulate_calcu(data_list, rule_dict):
    rise_cnt = 0
    fall_cnt = 0
    money = round(float(rule_dict['money']), 2)
    money_pool = round(float(rule_dict['money_limit']), 2) - money
    last_cnt = 0
    for data_index in data_list:
        per = float(data_index[2].replace('%','')) / 100
        money += money * per
        if (per > 0):
            rise_cnt += 1
        elif (per < 0):
            fall_cnt += 1
        
        if rise_cnt >= rule_dict['rise_sell']:
            rise_cnt = 0
            fall_cnt = 0
            sell_money = money * float(rule_dict['sell_per'])
            if last_cnt < 7:
                ti = sell_money * 0.015
                sell_money += ti
            else:
                ti = sell_money * 0.0015
                sell_money += ti
            if ti > money * per:
                continue
            money -= sell_money
            money_pool += sell_money
            #print ('[%s] money[%f] per[%f] --sell[%f(%f)]->  pool[%f]'%(data_index[0], money, per, sell_money, ti, money_pool))
            #print ('%s,%s,-1'%(data_index[0], data_index[1]))
            last_cnt = 0
        elif fall_cnt >= rule_dict['fall_buy']:
            rise_cnt = 0
            fall_cnt = 0
            buy_money = money * float(rule_dict['buy_per'])
            ti = buy_money * 0.001
            temp = buy_money + ti
            if temp > money_pool:
                buy_money = money_pool / 1.001
                ti = buy_money * 0.001
            money += buy_money
            money_pool -= buy_money + ti
            #print ('[%s] money[%f] per[%f] <-buy[%f(%f)]--  pool[%f]'%(data_index[0], money, per, buy_money, ti, money_pool))
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

    return money + money_pool


def run_simulator(data_list, base_dict, max_per):
    start_up = round(float(base_dict['money_limit']), 2)
    final_money = round(simulate_calcu(data_list, base_dict), 2)
    rise_per = (final_money - start_up) / start_up
    rise_per_str = str(round(100 * rise_per, 2)) + '%'
    if rise_per > max_per:
        max_per = rise_per
        print ('rise_sell[%d] sell_per[%f] fall_buy[%d] buy_per[%f]'%(
                base_dict['rise_sell'], base_dict['sell_per'], 
                base_dict['fall_buy'], base_dict['buy_per']))
        print ('[%f] --> [%f] ----------> Per[%s]'%(start_up, final_money, rise_per_str))

    return max_per

def main():
    base_dict = {
        'money' : 10000,
        'money_limit' : 100000,
        'rise_sell' : 4,
        'sell_per' : 0.9,
        'fall_buy' : 2,
        'buy_per' : 1.1,
    }

    data_list = []
    DBdict = spi_req.request_net_clean('161725', 30)
    for index in DBdict:
        temp = [index['FSRQ'], index['DWJZ'], index['JZZZL'] + '%']
        data_list.insert(0, temp)

    max_per = -100.0
    
    
    rise_sell = 2
    fall_buy = 2
    sell_per = 0.5
    buy_per = 1.0
    
    for rise_sell in range(2, 8):
        for fall_buy in range(2, 8):
            for sell_per in range(1, 10):
                for buy_per in range(1, 20):
                    base_dict['rise_sell'] = rise_sell
                    base_dict['fall_buy'] = fall_buy
                    base_dict['sell_per'] = sell_per / 10
                    base_dict['buy_per'] = buy_per / 10
                    max_per = run_simulator(data_list, base_dict, max_per)
    
    #max_per = run_simulator(data_list, base_dict, max_per)

if __name__ == '__main__':
    main()

import re
import subprocess
import multiprocessing
import sys
import time
import signal
import threading
import binascii
import string
import csv
import codecs
import paramiko
import xlwt
import threading
import copy
from scp import SCPClient
from socket import *
from multiprocessing import Process,Manager

distance_dict = {'1米':[0], '2米':[0], '3米':[0], 
                '4米':[0], '5米':[0], '6米':[0], 
                '7米':[0], '8米':[0], '9米':[0], 
                '10米':[0], '11米':[0]}
obu_dict = {'黑OBU':copy.deepcopy(distance_dict), '白OBU':copy.deepcopy(distance_dict)}
ant_dict = {'天线1':copy.deepcopy(obu_dict), '天线2':copy.deepcopy(obu_dict)}
total_dict = {'车道1':copy.deepcopy(ant_dict), '车道2':copy.deepcopy(ant_dict)}

finish_cnt = 0


def enqueen_info(dict, index, element):
    dict_tmp = {index : element}
    dict.update(dict_tmp)

def write_sheet(sheet, row, element):
    count = 0
    if type(element) == type(['']):
        for index in element:
            sheet.write(row, count, index)
            count += 1
    else:
        sheet.write(row, count, element)
    return (row + 1)


def rssr_get_list(lane, ant, obu, distance):
    if lane == '1':
        lane_dict_each = total_dict.get('车道1', 'NULL')
    else:
        lane_dict_each = total_dict.get('车道2', 'NULL')

    if type(lane_dict_each) == type('NULL'):
        print ("Error: [%s]无法获取车道字典"%(FileName))
        exit()
    else:
        if ant == '1':
            ant_dict_each = ant_dict.get('天线1', 'NULL')
        else:
            ant_dict_each = ant_dict.get('天线2', 'NULL')

    if type(ant_dict_each) == type('NULL'):
        print ("Error: [%s]无法获取天线字典"%(FileName))
        exit()
    else:
        if obu == '黑':
            obu_dict_each = obu_dict.get('黑OBU', 'NULL')
        else:
            obu_dict_each = obu_dict.get('白OBU', 'NULL')

    if type(obu_dict_each) == type('NULL'):
        print ("Error: [%s]无法获取OBU字典"%(FileName))
        exit()
    else:
        if distance == '1米':
            distance_list_each = distance_dict.get('1米', 'NULL')
        elif distance == '2米':
            distance_list_each = distance_dict.get('2米', 'NULL')
        elif distance == '3米':
            distance_list_each = distance_dict.get('3米', 'NULL')
        elif distance == '4米':
            distance_list_each = distance_dict.get('4米', 'NULL')
        elif distance == '5米':
            distance_list_each = distance_dict.get('5米', 'NULL')
        elif distance == '6米':
            distance_list_each = distance_dict.get('6米', 'NULL')
        elif distance == '7米':
            distance_list_each = distance_dict.get('7米', 'NULL')
        elif distance == '8米':
            distance_list_each = distance_dict.get('8米', 'NULL')
        elif distance == '9米':
            distance_list_each = distance_dict.get('9米', 'NULL')
        elif distance == '10米':
            distance_list_each = distance_dict.get('10米', 'NULL')
        else:
            distance_list_each = distance_dict.get('11米', 'NULL')
    if type(distance_list_each) == type('NULL'):
        print ("Error: [%s]无法获取距离列表"%(FileName))
        exit()
    else:
        return distance_list_each


def rssi_select(FileName):
    global finish_cnt

    name_split = FileName.split('-', 3)
    
    lane = name_split[0][-1:]
    ant = name_split[1][-1:]
    obu = name_split[2][:1]
    distance = name_split[3][:name_split[3].find('.txt')]
    #print ('lane=%s  ant=%s  obu=%s  distance=%s'%(lane, ant, obu, distance))

    list = []
    #print (list)

    with open(FileName, 'r') as f:
        total_data = ''
        for line in f.readlines():
            total_data += line[line.find(']'):]
        total_data = total_data.strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').replace(']', '').strip()
        data_split = total_data.split('FFFF')
        del data_split[0]
        for data_index in data_split:
            date_pick = data_index[data_index.find('18'):]
            if date_pick[2:4] == '23':
                adc_str = date_pick[8:12]
                continue
            elif date_pick[2:4] == '22':
                adc_str = date_pick[16:20]
            else:
                continue
            hex_bytes = bytearray.fromhex(adc_str)
            if len(hex_bytes) == 1:
                adc_value = hex_bytes[0]
            elif len(hex_bytes) == 2:
                adc_value = hex_bytes[0] * 256 + hex_bytes[1]
            list.append(adc_value)
    f.close()

    total_dict['车道%s'%(lane)]['天线%s'%(ant)]['%sOBU'%(obu)]['%s'%(distance)] = list
    finish_cnt = finish_cnt + 1

def excel_write(FileName):
    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet('My sheet', cell_overwrite_ok = True)
    worksheet.write_merge(0, 0, 0, 43, '车道1')
    worksheet.write_merge(0, 0, 44, 87, '车道2')
    
    worksheet.write_merge(1, 1, 0, 21, '天线1')
    worksheet.write_merge(1, 1, 22, 43, '天线2')
    worksheet.write_merge(1, 1, 44, 65, '天线1')
    worksheet.write_merge(1, 1, 66, 87, '天线2')
    
    worksheet.write_merge(2, 2, 0, 10, '黑色OBU')
    worksheet.write_merge(2, 2, 11, 21, '白色OBU')
    worksheet.write_merge(2, 2, 22, 32, '黑色OBU')
    worksheet.write_merge(2, 2, 33, 43, '白色OBU')
    worksheet.write_merge(2, 2, 44, 54, '黑色OBU')
    worksheet.write_merge(2, 2, 55, 65, '白色OBU')
    worksheet.write_merge(2, 2, 66, 76, '黑色OBU')
    worksheet.write_merge(2, 2, 77, 87, '白色OBU')
    
    title_list = []
    for i in range(8):
        title_list += ['1米', '2米', '3米', '4米', '5米', '6米', '7米', '8米', '9米', '10米', '11米']
    row = write_sheet(worksheet, 3, title_list)

    i = 0
    for lane_index in total_dict:
        for ant_index in total_dict[lane_index]:
            for obu_index in total_dict[lane_index][ant_index]:
                for distance_index in total_dict[lane_index][ant_index][obu_index]:
                    j = 5
                    sum = 0
                    for adc_value in total_dict[lane_index][ant_index][obu_index][distance_index]:
                        sum = sum + adc_value
                        worksheet.write(j, i, adc_value)
                        j = j + 1
                    if j == 5:
                        worksheet.write(4, i, '0(平均值)')
                    else:
                        worksheet.write(4, i, '%.2f(平均值)'%(sum / (j - 5)))
                    i = i + 1
    
    
    workbook.save(FileName.replace('.txt', '') + '_result.xls')
 
if __name__ == "__main__":
    file_argv = sys.argv
    del file_argv[0]

    for file_index in file_argv:
        if file_index.find('.txt') == (-1):
            print("文件输入有误,应输入[xxxx.txt]")
            exit()
        try:
            threading.Thread(target = rssi_select, args = (file_index, )).start()
        except:
            print ("Error: [%s]无法启动线程"%(file_index))

    while finish_cnt != len(file_argv):
        time.sleep(1)
    
    excel_write('Res')
    

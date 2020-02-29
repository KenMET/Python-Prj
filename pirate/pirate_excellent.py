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
from scp import SCPClient
from socket import *
from multiprocessing import Process,Manager

shell_name = 'pirate_arm.py'
scp_dir = '/root/Rfu_Logs'
shell_date = '2020-01-02 V03'

port = 3002
bufsiz = 1024 * 31
ver_len = 10
ip_len = 4
update_shell_flag = 0
old_shell_name = 'pirate_arm.py'
local_config_file = 'all_config.txt'
config_count = 4

def enqueen_info(dict, index, list):
    dict_tmp = {index : list}
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

def local_read_config(config_dict):
    with open(local_config_file, 'r') as f:
        for line in f.readlines():
            ip_mix = line.split(',', config_count + 1)
            if len(ip_mix) == (config_count + 1):
                ip_major = ip_mix[0].strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()
                grantry = ip_mix[1].strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()
                direction = ip_mix[2].strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()
                server_ip = ip_mix[3].strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()
                hex_code = ip_mix[4].strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()
            else:
                print (line + ' Read Skip')
                continue
            enqueen_info(config_dict, ip_major, [grantry, direction, server_ip, hex_code])

def dequeen_write(dict, dict_residue, ip_list_file):
    config_dict = {}
    local_read_config(config_dict)
    common_title = ['互通方向', '查询时间','状态','主机IP','备机IP','总成功率']
    share_title = ['设备类型', '成功率', '接入总数', '成功总数','被拒总数', '无卡', '军车',
            'b4-err[01]', 'b4-err[05]', 'b4-err[07]', 'b4-err[08]', 'b4-err[09]',
            'b4-err[0b]', 'b4-err[0c]', 'b4-err[0d]', 'b4-err[0e]',
            'b5-err[01]', 'b5-err[03]', 'b5-err[04]', 'b5-err[05]', 'b5-err[06]',
            'b5-err[07]', 'b5-err[0c]', 'b5-err[0d]', 'b5-err[0e]', 'b5-err[0f]',
            'b7-err[01]', 'b7-err[03]', 'b7-err[04]', 'b7-err[05]']
    print ('\n')
    ip = ['','']
    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet('My sheet', cell_overwrite_ok = True)
    row = write_sheet(worksheet, 0, common_title + share_title)
    with open(ip_file, 'r') as f:
        for line in f.readlines():
            ip_mix = line.split(',', 3)
            if len(ip_mix) == 2:
                ip[0] = ip_mix[0].strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()
                ip[1] = ip_mix[1].strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()
            else:
                print ('写文件，行内容不完整[%s]'%(line))
                continue

            if dict_residue.get(ip[0], 0) == 0:
                print ('%s 进程超时'%(ip[0]))
            config_list = config_dict.get(ip[0], ['门架编号未知','互通方向未知','服务器IP未知','HEX编号未知'])
            direction = config_list[1]
            tmp_list = dict.get(ip[0], ['NULL', '未知', ip[0], ip[1]])
            tmp_list = [direction] + tmp_list
            if len(tmp_list) < 2:
                print (ip[0] + ' Len Err' + str(tmp_list))
            if tmp_list[1] != 'NULL':
                row = write_sheet(worksheet, row, tmp_list)
                #row = write_sheet(worksheet, row, tmp_list[:len(common_title)+len(share_title)])
                #row = write_sheet(worksheet, row, ['','','','','','']+tmp_list[len(common_title)+len(share_title):])
                #for index in range(len(common_title)):
                #    worksheet.write_merge(row - 2, row - 1, index, index, tmp_list[index])
            else:
                row = write_sheet(worksheet, row, tmp_list)
    workbook.save(ip_list_file.replace('.txt', '') + '_trade_result.xls')

def check_alive(ip):
    if ip == 'NULL':
        return True
    count = 5
    timeout = 10
    result=local_cmd('ping -c %d -w %d %s'%(count,timeout,ip))
    regex=re.findall(b'100% packet loss',result)

    if len(regex)==0:
        test = result[result.find(b'min/avg/max/mdev = '):]
        test = test[test.find(b' = ') + 3: test.find(b' ms')]
        time = test.split(b'/', 4)
        avg_time = float(time[1])
        if avg_time > 200:
            print (ip + '  High time delay[' + str(avg_time) + ']')
            return False
        return True
    else:
        return False

def local_cmd(cmd):
    p = subprocess.Popen(cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)
    return p.stdout.read()

def copy_python(ssh_client, ip, date):
    if update_shell_flag == 1:
        rm_cmd = 'rm -rf %s/%s'%(scp_dir, old_shell_name)
        stdin,stdout,stderr = ssh_client.exec_command(rm_cmd)
        out_info = stdout.readlines()
    scp_client = SCPClient(ssh_client.get_transport(), socket_timeout = 15)
    re_try = 5
    while re_try > 0:
        stdin,stdout,stderr = ssh_client.exec_command('ls %s'%(scp_dir))
        res = stdout.readlines()
        if 'pirate_arm.py\n' in res:
            stdin,stdout,stderr = ssh_client.exec_command('cat %s/%s |grep "%s"'%(scp_dir, shell_name, shell_date))
            res = stdout.readlines()
            if len(res) == 1 and res[0].find('No such file or directory') == (-1):
                scp_client.close()
                return True
            else:
                scp_client.put(shell_name, scp_dir)
                print (ip + ' Instead Python done')
                time.sleep(1)
        else:
            scp_client.put(shell_name, scp_dir)
            print (ip + ' New Dev,Copy Python done')
            time.sleep(1)
    scp_client.close()
    return False

def major_bkup_caculat(major_obu, major_cpc, bkup_obu, bkup_cpc, excu_status):
    commit_obu = {}
    commit_cpc = {}
    if excu_status[0] == 1:
        for index in major_obu:
            major_num = major_obu.get(index, 0)
            bkup_num = bkup_obu.get(index, 0)
            enqueen_info(commit_obu, index, major_num + bkup_num)
        for index in major_cpc:
            major_num = major_cpc.get(index, 0)
            bkup_num = bkup_cpc.get(index, 0)
            enqueen_info(commit_cpc, index, major_num + bkup_num)
    elif excu_status[1] == 1:
        for index in bkup_obu:
            major_num = major_obu.get(index, 0)
            bkup_num = bkup_obu.get(index, 0)
            enqueen_info(commit_obu, index, major_num + bkup_num)
        for index in bkup_cpc:
            major_num = major_cpc.get(index, 0)
            bkup_num = bkup_cpc.get(index, 0)
            enqueen_info(commit_cpc, index, major_num + bkup_num)
    obu_total = commit_obu.get('接入总数', 0)
    cpc_total = commit_cpc.get('接入总数', 0)
    obu_trade_ok = commit_obu.get('交易成功总数', 0)
    cpc_trade_ok = commit_cpc.get('交易成功总数', 0)
    obu_refusal = commit_obu.get('主动拒绝总数', 0)
    cpc_refusal = commit_cpc.get('主动拒绝总数', 0)
    obu_no_card = commit_obu.get('无卡数', 0)
    obu_army = commit_obu.get('军车数', 0)
    cpc_army = commit_cpc.get('军车数', 0)
    obu_per = 0
    cpc_per = 0
    total_per = 0
    if (obu_total - obu_refusal - obu_no_card - obu_army) > 0:
        obu_per = (obu_trade_ok / (obu_total - obu_refusal - obu_no_card - obu_army)) * 100
    if (cpc_total - cpc_refusal - cpc_army) > 0:
        cpc_per = (cpc_trade_ok / (cpc_total - cpc_refusal - cpc_army)) * 100
    if (obu_total + cpc_total - obu_refusal - cpc_refusal - obu_no_card - cpc_army - obu_army) > 0:
        total_per = ((obu_trade_ok + cpc_trade_ok) / \
            (obu_total + cpc_total - obu_refusal - cpc_refusal - obu_no_card - cpc_army - obu_army)) * 100
    return commit_obu, commit_cpc, '%.2f%%'%(total_per), '%.2f%%'%(obu_per), '%.2f%%'%(cpc_per)

def analyze_info(ssh_client, date_str):
    stdin,stdout,stderr = ssh_client.exec_command('python %s/%s %s/info_20%s.log'%(scp_dir, shell_name, scp_dir, date_str))
    res = stdout.readlines()
    obu_result = {}
    cpc_result = {}
    emnu_list = ['接入总数','交易成功总数','主动拒绝总数','无卡数','军车数',
        'b4-err[01]','b4-err[05]','b4-err[07]','b4-err[08]','b4-err[09]','b4-err[0b]',
        'b4-err[0c]','b4-err[0d]','b4-err[0e]','b5-err[01]','b5-err[03]','b5-err[04]',
        'b5-err[05]','b5-err[06]','b5-err[07]','b5-err[0c]','b5-err[0d]','b5-err[0e]',
        'b5-err[0f]','b7-err[01]','b7-err[03]','b7-err[04]','b7-err[05]']
    emnu_num = len(emnu_list)
    if len(res) == 1:
        list = res[0].replace(' ', '').replace('[', '').replace(']', '').replace('"', '').replace("'", '').replace("\n", '')
        element_split = list.split(',')
        for i in range(emnu_num):
            enqueen_info(obu_result, emnu_list[i], int(element_split[i]))
        for i in range(emnu_num, emnu_num * 2):
            enqueen_info(cpc_result, emnu_list[i - emnu_num], int(element_split[i]))
    return obu_result, cpc_result


def check_trade(ip_major, ip_bkup, ping_status):
    tmp = []
    major_exist_flag = 0
    bkup_exist_flag = 0

    ssh_major = paramiko.SSHClient()
    ssh_major.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
    ssh_bkup = paramiko.SSHClient()
    ssh_bkup.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
    if ping_status[0] < 1:
        try:
            ssh_major.connect(ip_major, 22, 'root', 'Cgutech@600', timeout=20)
            major_exist_flag = 1
        except:
            print ("\033[31m%s  SSH Err\033[0m" %(ip_major))
    if ip_bkup != 'NULL' and ping_status[1] < 1:
        try:
            ssh_bkup.connect(ip_bkup, 22, 'root', 'Cgutech@600', timeout=20)
            bkup_exist_flag = 1
        except:
            print ("\033[31m%s  SSH Err\033[0m" %(ip_bkup))
    
    python_excu_sta = [0, 0]
    enum = []
    obu_result_major = {}
    cpc_result_major = {}
    obu_result_bkup = {}
    cpc_result_bkup = {}
    date_cmd = 'date +%y%m%d'
    try:
        if ping_status[0] < 1 and major_exist_flag == 1:
            stdin,stdout,stderr = ssh_major.exec_command(date_cmd)
            date = stdout.readlines()
            date_str = date[0].strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()
            cp_res = copy_python(ssh_major, ip_major, date_str)
            if cp_res == True:
                obu_result_major, cpc_result_major = analyze_info(ssh_major, date_str)
                python_excu_sta[0] = 1
    except:
        print ("\033[31m%s  analyze Err\033[0m" %(ip_major))

    try:
        if ip_bkup != 'NULL' and ping_status[1] == 0 and bkup_exist_flag == 1: 
            stdin,stdout,stderr = ssh_bkup.exec_command(date_cmd)
            date = stdout.readlines()
            date_str = date[0].strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()
            cp_res = copy_python(ssh_bkup, ip_bkup, date_str)
            if cp_res == True:
                obu_result_bkup, cpc_result_bkup = analyze_info(ssh_bkup, date_str)
                python_excu_sta[1] = 1
    except:
        print ("\033[31m%s  analyze Err\033[0m" %(ip_bkup))

    commit_obu, commit_cpc, total_per, obu_per ,cpc_per = major_bkup_caculat(obu_result_major, cpc_result_major, obu_result_bkup, cpc_result_bkup, python_excu_sta)
    #print ('[%s:%s][total:%s][obu:%s][cpc:%s]'%(ip_major, ip_bkup, total_per, obu_per, cpc_per))
    enum = [total_per,
            'OBU', obu_per, commit_obu.get('接入总数', 0), commit_obu.get('交易成功总数', 0),
            commit_obu.get('主动拒绝总数', 0), commit_obu.get('无卡数', 0),commit_obu.get('军车数', 0),
            commit_obu.get('b4-err[01]', 0), commit_obu.get('b4-err[05]', 0), commit_obu.get('b4-err[07]', 0),
            commit_obu.get('b4-err[08]', 0), commit_obu.get('b4-err[09]', 0), commit_obu.get('b4-err[0b]', 0),
            commit_obu.get('b4-err[0c]', 0), commit_obu.get('b4-err[0d]', 0), commit_obu.get('b4-err[0e]', 0),
            commit_obu.get('b5-err[01]', 0), commit_obu.get('b5-err[03]', 0), commit_obu.get('b5-err[04]', 0),
            commit_obu.get('b5-err[05]', 0), commit_obu.get('b5-err[06]', 0), commit_obu.get('b5-err[07]', 0),
            commit_obu.get('b5-err[0c]', 0), commit_obu.get('b5-err[0d]', 0), commit_obu.get('b5-err[0e]', 0),
            commit_obu.get('b5-err[0f]', 0), commit_obu.get('b7-err[01]', 0), commit_obu.get('b7-err[03]', 0),
            commit_obu.get('b7-err[04]', 0), commit_obu.get('b7-err[05]', 0),
            'CPC', cpc_per, commit_cpc.get('接入总数', 0), commit_cpc.get('交易成功总数', 0),
            commit_cpc.get('主动拒绝总数', 0), commit_cpc.get('无卡数', 0), commit_cpc.get('军车数', 0),
            commit_cpc.get('b4-err[01]', 0), commit_cpc.get('b4-err[05]', 0), commit_cpc.get('b4-err[07]', 0),
            commit_cpc.get('b4-err[08]', 0), commit_cpc.get('b4-err[09]', 0), commit_cpc.get('b4-err[0b]', 0),
            commit_cpc.get('b4-err[0c]', 0), commit_cpc.get('b4-err[0d]', 0), commit_cpc.get('b4-err[0e]', 0),
            commit_cpc.get('b5-err[01]', 0), commit_cpc.get('b5-err[03]', 0), commit_cpc.get('b5-err[04]', 0),
            commit_cpc.get('b5-err[05]', 0), commit_cpc.get('b5-err[06]', 0), commit_cpc.get('b5-err[07]', 0),
            commit_cpc.get('b5-err[0c]', 0), commit_cpc.get('b5-err[0d]', 0), commit_cpc.get('b5-err[0e]', 0),
            commit_cpc.get('b5-err[0f]', 0), commit_cpc.get('b7-err[01]', 0), commit_cpc.get('b7-err[03]', 0),
            commit_cpc.get('b7-err[04]', 0), commit_cpc.get('b7-err[05]', 0),]

    if major_exist_flag == 1 and (bkup_exist_flag == 1 or ping_status[1] == 2):
        tmp = [date_str, '网络正常', ip_major, ip_bkup] + enum
    elif major_exist_flag == 1 and ((bkup_exist_flag == 0 and ping_status[1] == 0) or ping_status[1] == 1):
        tmp = [date_str, '备机网络异常', ip_major, ip_bkup] + enum
    elif major_exist_flag == 0 and (bkup_exist_flag == 1 and ping_status[1] == 0):
        tmp = [date_str, '主机网络异常', ip_major, ip_bkup] + enum
    elif major_exist_flag == 0 and ((bkup_exist_flag == 0 and ping_status[1] == 0) or ping_status[1] == 1):
        tmp = [date_str, '主备网络均异常', ip_major, ip_bkup] + enum

    if major_exist_flag == 1:
        ssh_major.close()
    if ip_bkup != 'NULL' and bkup_exist_flag == 1:
        ssh_bkup.close()
    return tmp

def pirater(dict, dict_residue, ip_major, ip_bkup):
    ping_status = [0, 0]
    if check_alive(ip_major) == False:
        ping_status[0] = 1
    if ip_bkup == 'NULL':
        ping_status[1] = 2
    elif check_alive(ip_bkup) == False and ip_bkup != 'NULL':
        ping_status[1] = 1

    if ping_status[0] == 1 and ping_status[1] != 0:
        if ip_bkup == 'NULL':
            enqueen_info(dict, ip_major, ['NULL', '省界控制器ping不通',ip_major, ip_bkup])
        else:
            enqueen_info(dict, ip_major, ['NULL', '主备机均ping不通',ip_major, ip_bkup])
    else:
        tmp_list = check_trade(ip_major, ip_bkup, ping_status)
        enqueen_info(dict, ip_major, tmp_list)
    
    dict_residue.update({ip_major : 1})
 
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("arg Err")
        exit()
    ip_file = sys.argv[1]
    manager = Manager()
    global_dict = manager.dict()
    global_residue = manager.dict()

    cmd_res = local_cmd('rm -rf log_mix/*')

    read_num = 0
    with open(ip_file, 'r') as f:
        for line in f.readlines():
            ip_mix = line.split(',', 3)
            if len(ip_mix) == 2:
                ip_major = ip_mix[0].strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()
                ip_bkup = ip_mix[1].strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()
            else:
                print ('[%s]该行格式不正确，跳过'%(line))
                continue
            if ip_major in global_residue:
                print ("重复的IP： %s     " %(ip_major))
                continue
            read_num = read_num + 1
            enqueen_info(global_residue, ip_major, 0)
            pt = multiprocessing.Process(target=pirater, args=(global_dict, global_residue, ip_major, ip_bkup, ))
            pt.start()
            print ("开始检查 [%s:%s]              \r" %(ip_major, ip_bkup), end = '')
            time.sleep(0.1)
        print ("检查结束，正在等待返回......            ")

    time_out = 0
    time_limit = 80 + read_num * 2
    while len(global_dict) < read_num and time_out < time_limit:
        time.sleep(1)
        time_out = time_out + 1
        print ('完成进度 [%d/%d] time:(%ds/%ds)\r'%(len(global_dict), read_num, time_out, time_limit), end='')


    dequeen_write(global_dict, global_residue, ip_file)
    

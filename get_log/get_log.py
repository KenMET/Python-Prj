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
import datetime
from scp import SCPClient
from socket import *
from multiprocessing import Process,Manager


scp_dir = '/root/Rfu_Logs'

def enqueen_info(dict, ip, list):
    dict_tmp = {ip : list}
    dict.update(dict_tmp)

def dequeen_write(dict, ip_list_file, file):
    writer = csv.writer(file)
    with open(ip_file, 'r') as f:
        for line in f.readlines():
            ip_check = line.strip()
            writer.writerow(dict.get(ip_check, [ip_check, '未知']))

def check_alive(ip):
    if ip == 'NULL':
        return True
    count = 5
    timeout = 10
    cmd = 'ping -c %d -w %d %s'%(count,timeout,ip)
    p = subprocess.Popen(cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)
    result=p.stdout.read()
    regex=re.findall(b'100% packet loss',result)

    if len(regex)==0:
        test = result[result.find(b'min/avg/max/mdev = '):]
        test = test[test.find(b' = ') + 3: test.find(b' ms')]
        time = test.split(b'/', 4)
        avg_time = float(time[1])
        if avg_time > 200:
            print (ip + '  High time delay[' + str(avg_time) + ']')
            #return False
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

def check_log(ssh_client, today_str, date_target):
    
    return False

def copy_log(ssh_client, ip, today_str, date_target):
    res = local_cmd('mkdir -p log_mix/%s'%(ip))
    scp_client = SCPClient(ssh_client.get_transport(), socket_timeout = 15)
    
    ls_cmd = 'ls %s |grep %s'%(scp_dir, today_str)
    stdin,stdout,stderr = ssh_client.exec_command(ls_cmd)
    result = stdout.readlines()
    
    re_try = 5
    while re_try > 0:
        if len(result) == 4: 
            res = local_cmd('ls log_mix/%s'%(ip))
            if res.find(str.encode('info_%s.log'%(today_str))) >= 0 and \
                res.find(str.encode('error_%s.log'%(today_str))) >= 0 and \
                res.find(str.encode('tarce_%s.log'%(today_str))) >= 0 and \
                res.find(str.encode('warn_%s.log'%(today_str))) >= 0:
                scp_client.close()
                return True
            else:
                scp_client.get('%s/info_%s.log'%(scp_dir, today_str), 'log_mix/%s/'%(ip))
                scp_client.get('%s/error_%s.log'%(scp_dir, today_str), 'log_mix/%s/'%(ip))
                scp_client.get('%s/tarce_%s.log'%(scp_dir, today_str), 'log_mix/%s/'%(ip))
                scp_client.get('%s/warn_%s.log'%(scp_dir, today_str), 'log_mix/%s/'%(ip))
                if today_str != date_target:
                    scp_client.get('%s/%s.tar.gz'%(scp_dir, date_target), 'log_mix/%s/'%(ip))
        elif len(result) == 2:
            res = local_cmd('ls log_mix/%s'%(ip))
            if res.find(str.encode('info_%s.log'%(today_str))) >= 0 and \
                res.find(str.encode('warn_%s.log'%(today_str))) >= 0:
                scp_client.close()
                return True
            else:
                scp_client.get('%s/info_%s.log'%(scp_dir, today_str), 'log_mix/%s/'%(ip))
                scp_client.get('%s/warn_%s.log'%(scp_dir, today_str), 'log_mix/%s/'%(ip))
                if today_str != date_target:
                    scp_client.get('%s/%s.tar.gz'%(scp_dir, date_target), 'log_mix/%s/'%(ip))
        else:
            print ('%s 日志数量不对[%s]'%(ip, str(result)))
        re_try -= 1

    scp_client.close()
    return False


def excu_detail(ip_major, date_str):
    try:
        ssh_major = paramiko.SSHClient()
        ssh_major.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
        ssh_major.connect(ip_major, 22, 'root', 'Cgutech@600', timeout=10)
    except:
        ssh_major.close()
        return [ip_major, 'Log Get Fail']

    date_cmd = 'date +%Y%m%d'
    stdin,stdout,stderr = ssh_major.exec_command(date_cmd)
    date = stdout.readlines()[0]
    today_str = date.strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '')
    
    if copy_log(ssh_major, ip_major, today_str, date_str) == False:
        print (ip + 'Get Log Err')
        ssh_major.close()
        return [ip_major, 'Log Get Fail']
    print (ip_major + '  Log Get Success       ')
    ssh_major.close()
    return [ip_major, 'Log Get Success']


def excu(dict, dict_residue, ip_major, date_str):
    if check_alive(ip_major) == False:
        print (ip_major + ' 有设备ping不通')
        enqueen_info(dict, ip_major, ['NULL', '有设备ping不通',ip_major])
    else:
        tmp_list = excu_detail(ip_major, date_str)
        enqueen_info(dict, ip_major, tmp_list)
    dict_residue.update({ip_major : 1})
 
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("arg Err")
        exit()
    ip_file = sys.argv[1]
    date_str = sys.argv[2]
    if len(date_str) != 8:
        print("Date Err ,Example:[20200112]")
        exit()
    
    manager = Manager()
    global_dict = manager.dict()
    global_residue = manager.dict()
    f_ret = codecs.open(ip_file.replace('.txt', '') + "_check_res.csv", "w+", 'utf_8_sig')
    writer = csv.writer(f_ret)
    writer.writerow(['IP','复位结果'])

    cmd_res = local_cmd('rm -rf log_mix/*')

    read_num = 0
    with open(ip_file, 'r') as f:
        for line in f.readlines():
            ip_major = line.strip().replace(' ', '').replace('\n', '').replace('\t', '').replace('\r', '').strip()
            if ip_major in global_residue:
                print ("重复的IP： %s     " %(ip_major))
                continue
            read_num = read_num + 1
            enqueen_info(global_residue, ip_major, 0)
            pt = multiprocessing.Process(target=excu, args=(global_dict, global_residue, ip_major, date_str, ))
            pt.start()
            time.sleep(0.1)
    time_out = 0
    time_limit = 100 + read_num * 8
    while len(global_dict) < read_num and time_out < time_limit:
        time.sleep(1)
        time_out = time_out + 1
        print ('完成进度 [%d/%d] time:(%ds/%ds)\r'%(len(global_dict), read_num, time_out, time_limit), end='')
    print ("拷贝完成         ")

    #print ("\033[32m 正在写入文件 \033[0m")
    dequeen_write(global_dict, ip_file, f_ret)
    #print ("\033[32m 写入完成 \033[0m")

    f_ret.close()
    

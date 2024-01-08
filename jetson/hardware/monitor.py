import hashlib
import os, sys
import json
import logging
import tempfile
import optparse
import datetime, time
import threading, multiprocessing, subprocess


py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/oled'%(py_dir))
sys.path.append(r'%s/CubeNanoLib'%(py_dir))

from oled import Yahboom_OLED
from CubeNanoLib import CubeNano

line_str = ['None', 'None', 'None', 'None']

def is_night_time():
    current_time = datetime.datetime.now().time()

    night_start = datetime.time(21, 0)  # 20:00
    night_end = datetime.time(8, 0)     # 8:00

    if night_start <= current_time or current_time < night_end:
        return True
    else:
        return False

# Read the CPU usage rate
def getCPULoadRate(index):
    count = 10
    total_last = 0
    idle_last = 0
    str_CPU = "CPU:0%"
    if index == 0:
        f1 = os.popen("cat /proc/stat", 'r')
        stat1 = f1.readline()
        data_1 = []
        for i in range(count):
            data_1.append(int(stat1.split(' ')[i+2]))
        total_last = data_1[0]+data_1[1]+data_1[2]+data_1[3] + \
            data_1[4]+data_1[5]+data_1[6]+data_1[7]+data_1[8]+data_1[9]
        idle_last = data_1[3]
    elif index == 4:
        f2 = os.popen("cat /proc/stat", 'r')
        stat2 = f2.readline()
        data_2 = []
        for i in range(count):
            data_2.append(int(stat2.split(' ')[i+2]))
        total_now = data_2[0]+data_2[1]+data_2[2]+data_2[3] + \
            data_2[4]+data_2[5]+data_2[6]+data_2[7]+data_2[8]+data_2[9]
        idle_now = data_2[3]
        total = int(total_now - total_last)
        idle = int(idle_now - idle_last)
        usage = int(total - idle)
        usageRate = int(float(usage / total) * 100)
        str_CPU = "CPU:" + str(usageRate) + "%"
        total_last = 0
        idle_last = 0
    return str_CPU

# Read system time
def getSystemTime():
    cmd = "date +%H:%M:%S"
    date_time = subprocess.check_output(cmd, shell=True)
    str_Time = str(date_time).lstrip('b\'')
    str_Time = str_Time.rstrip('\\n\'')
    # print(date_time)
    return str_Time

# Read the memory usage
def getUsagedRAM():
    #cmd = "free | awk 'NR==2{printf \"RAM:%2d%% -> %.1fGB \", 100*($2-$7)/$2, ($2/1048576.0)}'"
    cmd = "free | awk 'NR==2{printf \"RAM:%2d%%\", 100*($2-$7)/$2}'"
    UseRam = subprocess.check_output(cmd, shell=True)
    str_UseRam = str(UseRam).lstrip('b\'')
    str_UseRam = str_UseRam.rstrip('\'')

    cmd = "free -h | awk 'NR==2{printf \"(%.1fGB Avail)\", $7}'"
    FreeRam = subprocess.check_output(cmd, shell=True)
    str_FreeRam = str(FreeRam).lstrip('b\'')
    str_FreeRam = str_FreeRam.rstrip('\'')

    return str_UseRam + str_FreeRam

# Read the SSD usage
def getUsagedDisk():
    cmd = "df -h |grep \"/dev/nvme\""
    Disk = subprocess.check_output(cmd, shell=True)
    disk_list = str(Disk, encoding='utf-8').split('\n')
    disk_str = 'Disk: '
    for disk_index in disk_list:
        if len(disk_index) == 0:
            continue
        disk_detail = disk_index.split()
        disk_str += '%s(%s Avail) '%(disk_detail[4], disk_detail[3])

    return disk_str.rstrip()

# Read the local IP address
def getLocalIP():
    ip = os.popen(
        "/sbin/ifconfig eth0 | grep 'inet' | awk '{print $2}'").read()
    ip = ip[0: ip.find('\n')]
    # ip = ''
    if(ip == '' or len(ip) > 15):
        ip = os.popen(
            "/sbin/ifconfig wlan0 | grep 'inet' | awk '{print $2}'").read()
        ip = ip[0: ip.find('\n')]
        if(ip == ''):
            ip = 'x.x.x.x'
    if len(ip) > 15:
        ip = 'x.x.x.x'
    
    return ip

def get_line_string(line):
    if (type(line) != type(0) or line < 0 or line > 3):
        return 'Line String Error'
    global line_str
    return line_str[line]

def set_line_string(line, text):
    if (type(line) != type(0) or line < 0 or line > 3):
        return False
    global line_str
    line_str[line] = text
    return True

def oled_flash(oled, scroll_speed=0):
    char_width = 6
    char2scroll = 20
    line_scroll_cnt = [0, 0, 0, 0]
    while True:
        oled.clear()
        if (is_night_time()):
            oled.refresh()
            time.sleep(60 * 5)
            continue
        for line_index in range(4):
            line_str = get_line_string(line_index)
            if (len(line_str) > char2scroll):
                limit = 0 - (len(line_str) + 6) * char_width
                oled.add_text(line_scroll_cnt[line_index], line_index*8, line_str)
                oled.add_text(abs(limit) + line_scroll_cnt[line_index], line_index*8, line_str)
                if (line_scroll_cnt[line_index] < limit):
                    line_scroll_cnt[line_index] = 0
                line_scroll_cnt[line_index] = line_scroll_cnt[line_index] - 1
            else:
                oled.add_line(line_str, line_index)
        oled.refresh()
        time.sleep(scroll_speed)




def oled_thread(logger, i2c_bus):
    oled = Yahboom_OLED(i2c_bus=7, clear=True)
    oled.begin()
    threading.Thread(target=oled_flash, args=(oled, 0.05)).start()
    while True:
        if (is_night_time()):
            time.sleep(60 * 5)  # 5 min to re-check
        else:
            set_line_string(0, 'Welcome to Jetson(' + getLocalIP() + ")")
            set_line_string(1, getCPULoadRate(4) + '   ' + getUsagedRAM())
            set_line_string(2, getUsagedDisk())
            set_line_string(3, "Time:" + getSystemTime())
            time.sleep(1)

def main(logger):
    bot = CubeNano(i2c_bus=7)
    bot.set_RGB_Effect(0) 
    oled_t = threading.Thread(target=oled_thread, args=(logger, 7, ))
    oled_t.start()
    oled_t.join()

if __name__ ==  '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_name = py_dir + '/' + py_name + '.log'
    fh = logging.FileHandler(log_name, mode='w')
    fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('Logger Creat Success')
    #logger.debug("this is debug") # Enable to modify fh.setLevel(logging.INFO) to logging.DEDBUG
    #logger.warning("this is warning")
    #logging.error("this is error")
    main(logger)

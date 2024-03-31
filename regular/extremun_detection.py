#!/usr/bin/python3
import hashlib
import os, sys
import json
import logging
import tempfile
import optparse
import datetime, time
import threading, multiprocessing, subprocess

# Helper libraries
import numpy as np
import matplotlib.pyplot as plt
import scipy

# Custom libraries
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../mysql'%(py_dir))
import db_cat as cbc
import db_dog as cbd
import db_peak as cbp
sys.path.append(r'%s/../common_api/xml_operator'%(py_dir))
import xml_operator as xo

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False

def get_last_quarter():
    date_now = datetime.datetime.now()
    quarter1 = datetime.datetime.strptime('%d-03-31'%(date_now.year), '%Y-%m-%d')
    quarter2 = datetime.datetime.strptime('%d-06-30'%(date_now.year), '%Y-%m-%d')
    quarter3 = datetime.datetime.strptime('%d-09-30'%(date_now.year), '%Y-%m-%d')
    quarter4 = datetime.datetime.strptime('%d-12-31'%(date_now.year), '%Y-%m-%d')
    if date_now < quarter1:
        return '%d-12-31'%(date_now.year-1)
    elif date_now < quarter2:
        return '%d-03-31'%(date_now.year)
    elif date_now < quarter3:
        return '%d-06-30'%(date_now.year)
    elif date_now < quarter4:
        return '%d-09-30'%(date_now.year)

def paint_data(dog_code, origin_data, h_label, padding_data=[]):
    fig = plt.figure(figsize=(10, 10))
    plt.plot(h_label, origin_data, color='black', label='Origin')
    
    if len(padding_data) != 0:
        top_padding = padding_data.get('top', [])
        value_label_r = [origin_data[i] for i in top_padding]
        h_label_r = [h_label[i] for i in top_padding]
        plt.scatter(h_label_r, value_label_r, c='r')
        
        bottom_padding = padding_data.get('bottom', [])
        value_label_g = [origin_data[i] for i in bottom_padding]
        h_label_g = [h_label[i] for i in bottom_padding]
        plt.scatter(h_label_g, value_label_g, c='g')

    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.title('[%s] Curve Plot'%(dog_code))
    fig.savefig('plot_peaks_%s.png'%(dog_code), facecolor='white')

def get_dog_origin(code, all_date=False):
    db = cbd.dogdb()

    dog_data = []
    dog_objs = db.queryDogMoneyFlowAll(code)
    for dog_data_index in dog_objs:
        temp_dict = db.get_dict_from_obj(dog_data_index)
        dog_data.append([temp_dict['Date'].strftime('%Y-%m-%d'),
            float(temp_dict['CloseValue']),
            float(temp_dict['MainPer']),
            float(temp_dict['BigPlusPer']),
            float(temp_dict['BigPer']),
            float(temp_dict['MiddPer']),
            float(temp_dict['LittlePer']),])

    origin_data = []
    date_list = []
    if not all_date:
        for index in dog_data:
            origin_data.append(index[1])    # CloseValue
            date_list.append(index[0])      # Date
    else:
        for index in dog_data:
            origin_data.append([index[1], index[2], index[3], index[4], index[5], index[6]])  
            date_list.append(index[0])      # Date
    return origin_data, date_list

def get_peaks(data, method=0):
    # Pre-process
    curve = np.array(data)
    init_data = curve[0]
    if init_data > 3.0:         # Normalization
        curve = curve / init_data
    mid_val = np.max(curve) - np.min(curve)
    flipped_curve = curve + (2 * (mid_val - curve))
    
    # Get peaks with method
    if method == 0:
        widths = 2.0
        window_size = 15.0
        min_distance = 10
        diff_ignore = 0.02      # 2%
        top_peaks = scipy.signal.find_peaks_cwt(curve, widths, window_size=window_size)
        bottom_peaks = scipy.signal.find_peaks_cwt(flipped_curve, widths, window_size=window_size)
        sorted_peaks = np.sort(np.concatenate((top_peaks, bottom_peaks)))
        for i in range(len(sorted_peaks) - 1):
            front = sorted_peaks[i]
            rear = sorted_peaks[i+1]
            if (rear - front) < min_distance:
                front_val = curve[front]
                rear_val = curve[rear]
                if abs(rear_val - front_val)/front_val < diff_ignore:
                    top_peaks = np.delete(top_peaks, np.where((top_peaks == front) | (top_peaks == rear)))
                    bottom_peaks = np.delete(bottom_peaks, np.where((bottom_peaks == front) | (bottom_peaks == rear)))

    top_padding_list = [i for i in top_peaks]
    bottom_padding_list = [i for i in bottom_peaks]
    return {'top':top_padding_list, 'bottom':bottom_padding_list}

def main(logger):
    db = cbp.peakdb()
    tables = db.queryTable()
    if ("dog_peaks" not in tables):
        db.create_peak_table()
    # db.closeSession() No need to close due to never open now.

    file_name = '%s/config.xml'%(py_dir)
    cfg = xo.operator(file_name)
    cfg_dict = cfg.walk_node(cfg.root_node)
    cat_list = cfg_dict.get('cat_list', {}).get('id', [])
    db = cbc.catdb()
    dog_code_list = []
    for cat_index in cat_list:
        dog_temp_list = db.queryCatHoldingByQuarter(cat_index, get_last_quarter())
        for index in dog_temp_list:
            dog_id = index.DogCodeQuarter[index.DogCodeQuarter.find(':')+1:]
            if (dog_id not in dog_code_list):
                dog_code_list.append(dog_id)
    db.closeSession()

    dog_extra_list = cfg_dict.get('dog_list', {}).get('id', [])
    for dog_extra_index in dog_extra_list:
        if (dog_extra_index not in dog_code_list):
            dog_code_list.append(dog_extra_index)
 
    db = cbp.peakdb()
    for code_index in dog_code_list:
        origin_data, date_list = get_dog_origin(code_index)
        padding_dict = get_peaks(origin_data)
        #paint_data(code_index, origin_data, date_list, padding_data=padding_dict)
        region = 'UNKNOW'
        if (is_number(code_index)):
            region = 'CN'
        else:
            region = 'US'
        
        input_index = padding_dict.get('bottom', [])
        output_index = padding_dict.get('top', [])

        peak_dict = {
            'ID':code_index,
            'Date':datetime.datetime.now(),
            'Type':region,
            'Input':[date_list[i] for i in input_index],
            'Output':[date_list[i] for i in output_index],
            'Reserve':'',
        }
        db.updateDogPeaksByID(code_index, peak_dict)
        logger.info('update item: %s'%(str(peak_dict)))
        time.sleep(0.5)
    db.closeSession()

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_name = py_dir + '/' + py_name + '.log'
    fh = logging.FileHandler(log_name, mode='a')
    fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('Logger Creat Success')

    logger.debug("this is debug") # Enable to modify fh.setLevel(logging.INFO) to logging.DEDBUG
    logger.warning("this is warning")
    logging.error("this is error")
    main(logger)

import os
import sys
import json
from flask import Flask, render_template, jsonify, request


py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
sys.path.append(r'%s/../common'%(py_dir))
from config import get_global_config, get_trade_list
from database import get_dog_realtime_min, get_dog_realtime_cnt, get_market_last

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # 对应之前的HTML文件

# 获取狗名字列表的API
@app.route('/api/get_dog_names')
def get_dog_names():
    dog_name_list = get_trade_list('us')
    print (dog_name_list)
    return jsonify(dog_name_list)

# 获取特定狗数据的API
@app.route('/api/get_dog_data')
def get_dog_data():
    dog_name = request.args.get('name')
    dog_data = get_dog_realtime_cnt(dog_name, 10)
    return jsonify(dog_data)

if __name__ == '__main__':
    app.run(host='172.19.62.218', port=8103, debug=True)

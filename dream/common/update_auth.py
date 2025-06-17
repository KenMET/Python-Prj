#!/bin/python3

# System lib
import os
import sys
import time
import hmac
import hashlib
import requests
import datetime
import argparse
from dateutil.relativedelta import relativedelta

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
from other import get_user_type
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_dream_secret as dbds
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def get_secret(user, q_type):
    db = dbds.db('dream_user')
    if (not db.is_table_exist()):
        #log.get().info('Quantitative table not exist, new a table...')
        db.create_secret_table()
    res = db.query_secret_by_type(q_type, user)
    if len(res) != 1:
        return
    app_key = res[0].App_Key
    app_secret = res[0].App_Secret
    access_token = res[0].Access_Token
    db.closeSession()
    return app_key, app_secret, access_token

def update_secret(user, q_type, app_key, app_secret, access_token):
    db = dbds.db('dream_user')
    temp_dict = {
        'Type' : '%s-%s'%(user, q_type),
        'App_Key' : app_key,
        'App_Secret' : app_secret,
        'Access_Token' : access_token,
    }
    flag = db.update_secret(temp_dict)
    db.closeSession()
    return flag

def sign(method, uri, headers, params, body, secret):
    ts = headers["X-Timestamp"]
    access_token = headers["Authorization"]
    app_key = headers["X-Api-Key"]
    mtd = method.upper()
    canonical_request = mtd + "|" + uri + "|" + params + "|authorization:" + access_token + "\nx-api-key:" + app_key + "\nx-timestamp:" + ts + "\n|authorization;x-api-key;x-timestamp|"
    if body != "":
        payload_hash = hashlib.sha1(body.encode("utf-8")).hexdigest()
        canonical_request = canonical_request + payload_hash
    sign_str = "HMAC-SHA256|" + hashlib.sha1(canonical_request.encode("utf-8")).hexdigest()
    signature = hmac.new(secret.encode('utf-8'), sign_str.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
    return "HMAC-SHA256 SignedHeaders=authorization;x-api-key;x-timestamp, Signature=" + signature

def refresh_token(app_key, app_secret, access_token):
    new_expiration_time = datetime.datetime.now() + relativedelta(months=+3)
    expired_at = new_expiration_time.isoformat(timespec='milliseconds') + 'Z'
    params = 'expired_at=' + expired_at

    headers = {}
    headers['X-Api-Key'] = app_key
    headers['Authorization'] = access_token
    headers['X-Timestamp'] =  str(time.time())
    headers['Content-Type'] = 'application/json; charset=utf-8'
    headers['X-Api-Signature'] = sign('GET', '/v1/token/refresh', headers, params, "", app_secret)
    response = requests.request('GET', "http://openapi.longportapp.com/v1/token/refresh" + '?' + params, headers=headers)
    full_data = response.json()
    if full_data['code'] == 0:
        token = full_data['data']['token']
        return token
    else:
        log.get().error('Token Refresh error: %s'%(str(full_data)))
        return None

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='a', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success')

    user = args.user
    q_type = args.type
    if user == '' or q_type == '':
        log.get().error('User or Type not specific...')
        return

    app_key, app_secret, access_token = get_secret(user, q_type)
    new_token = refresh_token(app_key, app_secret, access_token)
    if new_token == None:
        log.get().error('Token refresh failed...')
        return
    log.get().info('New Token: %s'%(new_token))
    #new_token = 'm_eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsb25nYnJpZGdlIiwic3ViIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNzU4MTQ3MjMxLCJpYXQiOjE3NTAxNjk2MzMsImFrIjoiIiwiYWFpZCI6MjAzMDc4NTQsImFjIjoibGJfcGFwZXJ0cmFkaW5nIiwibWlkIjoxMjgwNDkyNCwic2lkIjoiVHFVOHpTbENFNEs3ZVNaMHVRN1E2QT09IiwiYmwiOjMsInVsIjowLCJpayI6ImxiX3BhcGVydHJhZGluZ18yMDMwNzg1NCJ9.EwDWgnFrbnde3xs5mYm17hO-VRUztcFMNUlfcV5moyG0BVx0Dq-nxZTFNj4PvNjFYrYiMax4TqoZL9q5vjI4s6dVem_OJIzADWPXEC7mhaFd1Tz8i5sl7GN27aVAhHr98wseEu-gCo6rLxU4NZkSNvyJxUr1ViJ9r7NX4GpPkcT_A663fcf60WUKdv0452R1kM5l185CnzRp8U9FP6sSDwd_kyeNQd7qqzJ3IJBUxgCGfeR7RtbEtLbe2VD3dtk6ern3RpLQU3I03Cg1FNfFRSz1S82NuwuQyr8ryQMO06VvhH-uZLx8RQVEN-pUqqkT4SzFvGUHAs_bsECY8uTM8mnNfHQN5l4DefIeGG7khtlCqXSpNP-iSZ9k3q1duf0_bl3Bro5eU7wKatqM3jOAEBF2mkVmrUoiEa1RF9oiWcV8EzxO9PPx1Rs97YgXfJ-pMOFXhy82q_VFBwrAEDTEj0w-ktBIxeMdTnN9QOxik4Hg7XHY5W9Qvn4KVC6lA40JN6rm0JyneXnaZwE3AOw9BE8iq5ZIf3pSDrbIRTSiqHhn815ZQsUT1t-Yhhuj5X4LArJlCFyE6TQ-7DiE1eP7rMkqGfB-XrBpdO5fy6x2pzuTXYIUSG7LZKpe0P74OhsZG-nO4mKQQgLsPw23s1bcDSnpbidY--5nqIFlhGtPJTY'

    flag = update_secret(user, q_type, app_key, app_secret, new_token)
    if (not flag):
        log.get().error('Quantitative table update failed for [%s][%s]...'%(user, q_type))
    else:
        log.get().info('Quantitative table update successful for [%s][%s]...'%(user, q_type))

if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for user import")
    
    # Append arguments
    parser.add_argument('--user', type=str, default='', help='')
    parser.add_argument('--type', type=str, default='', help='')
    #parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)


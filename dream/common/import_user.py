#!/bin/python3

# System lib
import os
import sys
import datetime
import argparse

# Customsized lib
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/'%(py_dir))
from other import get_user_type
sys.path.append(r'%s/../../mysql'%(py_dir))
import db_dream_secret as dbds
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='a', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success')

    user_name = 'kanos'
    user_type = 'formal'  # simulation or formal

    api_key = '4322cccc27e178df4e5169eb1403a903'
    api_secret = 'e8d5674918efe0b7a788fdd3d9ed6cdf619264545a07533301bf34da3763dbcc'
    api_token = 'm_eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsb25nYnJpZGdlIiwic3ViIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNzUwMDc3NTYwLCJpYXQiOjE3NDIzMDE1NTksImFrIjoiNDMyMmNjY2MyN2UxNzhkZjRlNTE2OWViMTQwM2E5MDMiLCJhYWlkIjoyMDMwMDQzMywiYWMiOiJsYiIsIm1pZCI6MTI4MDQ5MjQsInNpZCI6ImNzQlZsa2ZxMTlac3dUN1AzcHcyL3c9PSIsImJsIjozLCJ1bCI6MCwiaWsiOiJsYl8yMDMwMDQzMyJ9.t_L8UMAS8m1QnTfOFruk5F6fgsmOuUcTHqR-P_yV0WQ1G17jOS6E5GfPc7ytB0Jh1Ga0oG4jzL34c1ph5VrehrpwMh_nlqmQqXqPb9vQ5sESuzUlixaVhDnK49xO5I99YieacC6s_dn2Pp1lw8ZQvvVQfr6PG_1KajHNotTb3DIqqWPs2MBwbgGHyj9d1tE7tlzH4XleC2F-89UcR2wzPAlJSFghm11SUP_uq7YCyUpF4uNDZ3aZkGlpMCVvz5Q4UzDnGkaGVBg60QdlwwrdHyjVtfQ4eS77k4zFSXmvKhRTs4IKBA7ikHwKKzVOS2GZFH4a-McKZcVl2YWiAfmKzYf1mBlaYFa5gZATqXHeNTseozqpHeBHIcmQmzvkfN18o7tctfAqTefTxqrgUH3uc6fEDiVkwc3CxTajoRneQsIZQPuTCzy6Ahm2IINV-34SaJndNxv55Fj-kcIDs5Ml2X5llE1qMHg88oum6kiyMZ7qXm-5Zoou2-z3XCihiaEpACfY7WGMemcjRXAEP9ri0IMrHyfJ94MNEa09GSRRKIjCC4anmvls5_pCNISIKz4TLyqqzlbUZezPncJza-Xp4_oM7x6pDs-tVIg3sea7i8T5cHTdOTwQpA4DgGzMGtPzTGfAVepAp7cmPhOEOgn7po0ewsxZo-i-MGzBZBmudQg'



    db = dbds.db('dream_user')
    if (not db.is_table_exist()):
        #log.get().info('Quantitative table not exist, new a table...')
        db.create_secret_table()

    temp_dict = {
        'Type' : get_user_type('-'),
        'App_Key' : api_key,
        'App_Secret' : api_secret,
        'Access_Token' : api_token,
    }

    #flag = db.insert_secret(temp_dict)
    flag = db.update_secret(temp_dict)
    if (not flag):
        log.get().error('Quantitative table update failed for [%s][%s]...'%(user_name, user_type))
    else:
        log.get().info('Quantitative table update successful for [%s][%s]...'%(user_name, user_type))


if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for user import")
    
    # Append arguments
    #parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')
    #parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)


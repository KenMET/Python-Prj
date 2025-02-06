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

sys.path.append(r'%s/../../mysql'%(py_dir))
import db_dream_secret as dbds
sys.path.append(r'%s/../../common_api/log'%(py_dir))
import log

def main(args):
    log.init('%s/../log'%(py_dir), py_name, log_mode='a', log_level='info', console_enable=True)
    log.get().info('Logger Creat Success')

    user_name = 'kanos'
    user_type = 'formal'

    api_key = '4322cccc27e178df4e5169eb1403a903'
    api_secret = 'e8d5674918efe0b7a788fdd3d9ed6cdf619264545a07533301bf34da3763dbcc'
    api_token = 'm_eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsb25nYnJpZGdlIiwic3ViIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNzQyMjExMTMxLCJpYXQiOjE3MzQ0MzUxMzAsImFrIjoiNDMyMmNjY2MyN2UxNzhkZjRlNTE2OWViMTQwM2E5MDMiLCJhYWlkIjoyMDMwMDQzMywiYWMiOiJsYiIsIm1pZCI6MTI4MDQ5MjQsInNpZCI6ImNVOXN3S1lGS0JEWTZOVTdiRno1ZGc9PSIsImJsIjozLCJ1bCI6MCwiaWsiOiJsYl8yMDMwMDQzMyJ9.xppc0Mp_S0BoqDbOBPQBmXjPwiFLuV_pLpBt4C8qb4cKmRofUrbb3Zl6d0eRBa4nkpni_sYlL9iH1qYwOBY3trXfOWsg9T3EWhUkGcd5lv4yAk3zabG5iFwsoIzgjpIeW8sH4m3MxC1xj61APRU6WjG7-WlOr6vxP2qatD7DSn63Q2A64FRjP7qGjK0Fp-TLeR3BEmC3IW9jUeGREAnw7g0yEqlj5WlADtUHxsBNX-czWNWYW_O2FWIaOV64kMdp8NarbtPRuxGifkO5ePCrDTGAns_cX_c6PfYHFkRCRaoN6Ya26Uk3Oe7fwWD365oArG56TfWaxf91nOzhv5F8znLfGYlYkphCNhqVR019M8pa9NioE0cSZUbKASOwLAIb_rijA70KSnWF7tnBSsYaHd8xyhWk-fBnSfitzlW5-Fywj-5YJJ5mpbyoM4L_GLCP7U9PnDeOnRP6SCaJDg5S4jB1-1avu9A-Ssc8Ma5jrW8uM_VJebIilH6NXdQsZ38-mrpx9OBQYOFForaPRrqGuoAFJfY_9f9k7Ouf9cP20oIZ3z1Iv7jb47iXNHPYZ9S6pRaBhcUqIte0Qw2syzhU2JMfofahvijyNl0HJ87pHdQCwsbYR8e5FjsCynrphmYjqonBC70DNdKU3NHdCeIm1ZZkK_aHjZl7wIv52aYJXGA'

    db = dbds.db('dream_user')
    if (not db.is_table_exist()):
        #log.get().info('Quantitative table not exist, new a table...')
        db.create_secret_table()

    temp_dict = {
        'Type' : '%s-%s'%(user_name, user_type),
        'App_Key' : api_key,
        'App_Secret' : api_secret,
        'Access_Token' : api_token,
    }

    flag = db.insert_secret(temp_dict)
    if (not flag):
        log.get().error('Quantitative table insert failed for [%s]...'%(user_name))
    else:
        log.get().info('Quantitative table insert successful for [%s]...'%(user_name))


if __name__ == '__main__':
    # Create ArgumentParser Object
    parser = argparse.ArgumentParser(description="A input module for user import")
    
    # Append arguments
    #parser.add_argument('--market', type=str, default='cn', help='Now supported: "cn"(default),"us"')
    #parser.add_argument('--test', type=bool, default=False, help='Test mode enable(True) or not(False as default)')
    
    # 解析命令行参数
    args = parser.parse_args()
    main(args)


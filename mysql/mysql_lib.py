#Create By Ken in 2020-03-17
#Modify Log:
#
#

import time
import datetime
import mysql.connector


class mysql_client:
    def __init__(self, host="1.2.3.4",user="ken", passwd="05310119"):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.db_connect = mysql.connector.connect(host=self.host,user=self.user, passwd=self.passwd)
        self.cursor = self.db_connect.cursor()

    def creat_db(self, data_base):
        self.cursor.execute("CREATE DATABASE IF NOT EXISTS %s"%(data_base))
    
    def select_db(self, data_base):
        self.cursor.execute("use %s"%(data_base))
    
    def delet_db(self, data_base):
        self.cursor.execute("DROP DATABASE IF EXISTS %s"%(data_base))

    def creat_tb(self, table, title_dict):
        if len(title_dict) < 1:
            return False
        first = False
        list_tmp = []
        for dict_index in title_dict:
            if type(title_dict[dict_index]) == type(0.1):
                var_type = 'FLOAT[6,3]'
            elif type(title_dict[dict_index]) == type(1):
                var_type = 'INT[10]'
            else:
                var_type = 'VARCHAR[255]'
            if first == False:
                main_key = dict_index
                main_key_type = var_type.replace('[','(').replace(']',')')
                first = True
            else:
                list_tmp.append(dict_index + ' ' + var_type)
        data_type = str(tuple(list_tmp)).replace("'", '').strip('(').strip(')')
        data_type = data_type.replace("]", ')').replace("[", '(')
        self.cursor.execute("CREATE TABLE IF NOT EXISTS %s (%s %s PRIMARY KEY, %s)"%(table, main_key, main_key_type, data_type))

    def delet_tb(self, table):
        self.cursor.execute("DROP TABLE IF EXISTS %s"%(table))

    def clear_tb(self, table):
        self.cursor.execute("DELETE FROM %s"%(table))

    #SELECT * FROM `sdm723414637_db`.`config` WHERE `Id` LIKE '%Ken%' AND `MoneyLimit` LIKE '%50%'
    def show_tb(self, table, key_dict):
        key_word = ''
        if type(key_dict) != type(None):
            if len(key_dict) != 0:
                key_word = 'where '
                for index in key_dict:
                    if len(key_word) > 10:
                        key_word += 'AND '
                    key_word += "%s LIKE '%%%s%%' "%(index, key_dict[index])
        self.cursor.execute("SELECT * FROM %s %s"%(table, key_word))
        return self.cursor.fetchall()

    #table: string
    #title_list:single list [...]
    #list_of_tuple: double_list[(...), (...), (...)]
    def insert(self, table, title_list, list_of_tuple, replace):
        if type(list_of_tuple) != type([0,]) or type(list_of_tuple[0]) != type((0,)):
            return False
        title_str = ', '.join(title_list)
        if replace == True:
            sql_cmd = 'INSERT INTO %s (%s) VALUES (%s)'%(table, title_str, ', '.join('%s' for i in range(len(title_list))))
            sql_cmd += ' ON DUPLICATE KEY UPDATE ' + ', '.join('%s=VALUES(%s)'%(index, index) for index in title_list)
        else:
            sql_cmd = 'INSERT IGNORE INTO %s (%s) VALUES (%s)'%(table, title_str, ', '.join('%s' for i in range(len(title_list))))
        self.cursor.executemany(sql_cmd, list_of_tuple)
    
    #UPDATE `sdm723414637_db`.`daily_Ken` SET `Name` = 'Test' WHERE `Name` = ''
    def update(self, db_name, table, title, orgin_value, dst_value):
        sql_cmd = "UPDATE `%s`.`%s` SET `%s` = '%s' WHERE `%s` = '%s'"%(db_name, table, title, dst_value, title, orgin_value)
        self.cursor.execute(sql_cmd)
        self.db_connect.commit()
        
    def flush(self):
        self.db_connect.commit()

    def close(self):
        self.cursor.close()


daily_db = {'Id':'', 'Name':'', 'Date':'', 'NetValue':'','Amplitude':'','BuyStatus':'','SellStatus':'', 'BuyRate':'', 'Money':'', 'RiseSellCnt':'', 'FallBuyCnt':'', 'LastActCnt':''}
config = {'Id':'', 'Name':'', 'StartMoney':'', 'MoneyLimit':'', 'RiseSell':'', 'SellPer':'', 'FallBuy':'', 'BuyPer':'', 'BuyRate':'',}
calcu_XXXXXX = {'DateRange':'', 'RiseSell':'', 'SellPer':'', 'FallBuy':'', 'BuyPer':'', 'FinalMoney':'', 'MaxPer':''}
fund_list = [
    '161725', '161028', '002168', '002979', '001629',
    '003096', '005609', '001593',
]

import os,sys
py_dir = os.path.dirname(os.path.realpath(__file__))
py_name = os.path.realpath(__file__)[len(py_dir)+1:-3]
sys.path.append(r'%s/../spider/'%(py_dir))

import spider_request as spiderRq


def main():
    total_db = {'name':'', 'id':'',
                'NetValue':'','Amplitude':'','BuyStatus':'','SellStatus':'', 'BuyRate':'',
                }
    mydb = mysql_client(host="sdm723414637.my3w.com",user="sdm723414637", passwd="WEIyuYAN2feiNot")
    #mydb.delet_db('Fund')
    #mydb.creat_db('Fund')
    mydb.select_db('sdm723414637_db')
    #mydb.creat_tb('Head_Table', total_db)

    mydb.delet_tb('config')
    mydb.creat_tb('config', config)
    mydb.delet_tb('daily_Stella')
    mydb.creat_tb('daily_Stella', daily_db)
    mydb.delet_tb('daily_Ken')
    mydb.creat_tb('daily_Ken', daily_db)
    #for index in fund_list:
    #    mydb.creat_tb('net_%s'%(index), net_XXXXXX)
    #    mydb.creat_tb('calcu_%s'%(index), calcu_XXXXXX)
    
    #mydb.update("sdm723414637_db", 'calcu_161725', 'DateRange', '2021-01-04 - 2021-02-03', '2021-01-04 - 2021-01-18')
    

    '''
    for index in fund_list:
        table_name = 'net_%s'%(index)
        title_list = []
        for title_index in net_XXXXXX:
            title_list.append(title_index)
        
        DBdict = spiderRq.request_net(index, 1500)
        for index in DBdict:
            temp = [index['FSRQ'], index['DWJZ'], index['LJJZ'], index['JZZZL']+'%', index['SGZT'], index['SHZT'], index['FHSP']]
            mydb.insert(table_name, title_list, [tuple(temp)], True)
    '''
    '''
    for index in fund_list:
        table_name = 'net_%s'%(index)
        title_list = []
        for title_index in net_XXXXXX:
            title_list.append(title_index)
        
        DBdict = spiderRq.request_net(index, 1500)
        for index in DBdict:
            temp = [index['FSRQ'], index['DWJZ'], index['LJJZ'], index['JZZZL']+'%', index['SGZT'], index['SHZT'], index['FHSP']]
            mydb.insert(table_name, title_list, [tuple(temp)], True)
    '''

    #mydb.delet_db('Test')
    #mydb.creat_db('Test')
    #mydb.select_db('Test')
    #mydb.creat_tb('test_tb', {'名字':'', '性别':'', '年龄':''})
    #title_list = ['名字','性别', '年龄']
    #list_of_tuple = [['1','2','3'],['A','B','C'],['!','@','#']]
    #mydb.insert('test_tb', title_list, list_of_tuple)
    #print (mydb.show_tb('test_tb'))

if __name__ == '__main__':
    main()

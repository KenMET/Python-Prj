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
        list_tmp = []
        for dict_index in title_dict:
            if type(title_dict[dict_index]) == type(''):
                var_type = 'VARCHAR[255]'
            elif type(title_dict[dict_index]) == type(0.1):
                var_type = 'FLOAT[6,3]'
            elif type(title_dict[dict_index]) == type(1):
                var_type = 'INT[10]'
            list_tmp.append(dict_index + ' ' + var_type)
        data_type = str(tuple(list_tmp)).replace("'", '').strip('(').strip(')')
        data_type = data_type.replace("]", ')').replace("[", '(')
        #self.cursor.execute("ALTER TABLE %s ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY"%(table))
        self.cursor.execute("CREATE TABLE IF NOT EXISTS %s (id INT AUTO_INCREMENT PRIMARY KEY, %s)"%(table, data_type))

    def delet_tb(self, table):
        self.cursor.execute("DROP TABLE IF EXISTS %s"%(table))

    def clear_tb(self, table):
        self.cursor.execute("DELETE FROM %s"%(table))

    def show_tb(self, table, key_dict):
        key_word = ''
        if len(key_dict) != 0:
            key_word = 'where '
            for index in key_dict:
                key_word += "%s='%s' "%(index, key_dict[index])
        self.cursor.execute("SELECT * FROM %s %s"%(table, key_word))
        return self.cursor.fetchall()

    def insert(self, table, title_list, list_of_tuple):
        if len(title_list) != len(list_of_tuple[0]):
            return False
        title_str = str(title_list).replace("'",'').replace('[','').replace(']','')
        sql_cmd = 'INSERT INTO %s (%s) VALUES (%s)'%(table, title_str, ''.join('%s, ' for i in range(len(title_list))))
        sql_cmd = sql_cmd[:-3] + ')'
        val = []
        for list_index in list_of_tuple:
            val.append(tuple(list_index))
        self.cursor.executemany(sql_cmd, val)
        #self.db_connect.commit()

    def insert_or_update(self, table, title_list, list_of_tuple, key_list, repalce_flag):
        key_dict = {}
        for key_index in key_list:
            key_dict.update({key_index:list_of_tuple[title_list.index(key_index)]})
        res_list = self.show_tb(table, key_dict)
        if len(res_list) == 0:
            self.insert(table, title_list, [list_of_tuple])
            return True
        elif len(res_list) != 1:
            return False
        if len(title_list) != len(list_of_tuple):
            return False
        if repalce_flag == False:
            return False
        tmp_str = 'SET '
        for i in range(len(title_list)):
            tmp_str += "%s = '%s', "%(title_list[i], list_of_tuple[i])
        sql_cmd = 'UPDATE %s '%(table) + tmp_str + " WHERE %s = '%s'"%(key_index, list_of_tuple[title_list.index(key_index)])
        sql_cmd = sql_cmd.replace(',  WHERE', ' WHERE')
        sql_cmd = sql_cmd.replace("['", "[").replace("']", "]").replace("', '", ", ")
        self.cursor.execute(sql_cmd)
        #self.db_connect.commit()
        
    def flush(self):
        self.db_connect.commit()

'''
def main():
    total_db = {'名字':'', '代号':'',
                '成立日期':'','最新规模':'','基金类型':'',
                '管理人':'','累计单位净值':'','近1月':'',
                '近3月':'','近6月':'','近1年':'','成立来':'',}
    mydb = mysql_client(host="182.61.47.202",user="root")
    #mydb.delet_db('Fund')
    mydb.creat_db('Fund')
    mydb.select_db('Fund')
    mydb.creat_tb('Head_Table', total_db)

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
'''
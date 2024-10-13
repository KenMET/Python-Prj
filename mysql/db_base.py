#!/bin/python3

# System lib
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import pymysql
import os

HOST = os.environ['DB_HOST']
PORT = int(os.environ['DB_PORT'])
USER = os.environ['DB_USER']
CODE = os.environ['DB_CODE']

class basedb(object):
    def __init__(self, DB_NAME) -> None:
        self.session = None
        self.db_class = {}
        self.engine = create_engine('mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(USER,CODE,HOST,PORT,DB_NAME))
        self.Base = declarative_base() 

    def openSession(self):
        if self.session is None: 
            self.connectdb()
        return self.session

    def closeSession(self):
        if self.session is None:
            self.session.close()

    def connectdb(self):
        mySession = sessionmaker(bind=self.engine) 
        self.session = mySession()

    def get_dict_from_obj(self, obj=None):
        if (obj == None):
            return None
        temp = {}
        #attr = [a for a in dir(obj) if not a.startswith('_') and not callable(getattr(obj, a))]
        #print ('********************************************')
        #for a in attr:
        #    print (a, getattr(obj, a), type(getattr(obj, a)))
        attr = [a for a in dir(obj) if not a.startswith('_') and not callable(getattr(obj, a)) and 
                (type(getattr(obj, a)) == type('strings') or
                type(getattr(obj, a)) == type(['list']) or
                type(getattr(obj, a)) == datetime.datetime or 
                type(getattr(obj, a)) == datetime.date)]
        for a in attr:
            temp.update({a:getattr(obj, a)})
        return temp

    def get_obj_from_dict(self, tmp_dict, obj=None): 
        if (obj == None):
            return None
        for a in tmp_dict:
            try:
                setattr(obj, a, tmp_dict[a])
            except:
                print ('get_obj_from_dict:[%s]:%s'%(a, tmp_dict[a]))
        return obj

    def queryTable(self):
        with self.engine.connect() as conn:
            table_list = []
            result = conn.execute(text("show tables"))
            for index in result:
                table_list.append(index[0])
            return table_list

    # Cannot use now....
    def dropTable(self, table_name):
        try:
            metadata = MetaData()
            # 反射获取表结构
            table = Table(table_name, metadata, autoload_with=self.engine)
            table.drop(self.engine)
            return True
        except Exception as e:
            return False
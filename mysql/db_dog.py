import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DATETIME, Text, VARCHAR
from sqlalchemy.orm import sessionmaker, relationship
import pymysql
import datetime
from pathlib import Path
import os
import time

HOSTNAME = '127.0.0.1'
DATABASE = 'kanos_dog'
PORT = 3306
USERNAME = 'root'
PASSWORD = '7cd0a058'
DB_URL = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(USERNAME,PASSWORD,HOSTNAME,PORT,DATABASE)
engine = create_engine(DB_URL)

Base = declarative_base(engine) 

class dogdb(object):
    def __init__(self) -> None:
        self.session = None
        self.dog_money_flow_class = {}

    def openSession(self):
        if self.session is None: 
            self.connectdb()
        return self.session

    def closeSession(self):
        if self.session is None:
            self.session.close()

    def connectdb(self):
        mySession = sessionmaker(bind=engine) 
        self.session = mySession()

    def get_dict_from_obj(self, obj):
        temp = {}
        #attr = [a for a in dir(obj) if not a.startswith('_') and not callable(getattr(obj, a))]
        #print ('********************************************')
        #for a in attr:
        #    print (a, getattr(obj, a), type(getattr(obj, a)))
        attr = [a for a in dir(obj) if not a.startswith('_') and not callable(getattr(obj, a)) and 
                (type(getattr(obj, a)) == type('strings') or
                type(getattr(obj, a)) == datetime.datetime or 
                type(getattr(obj, a)) == datetime.date)]
        for a in attr:
            temp.update({a:getattr(obj, a)})
        return temp

    def get_obj_from_dict(self, dog_dict, obj): 
        for a in dog_dict:
            try:
                setattr(obj, a, dog_dict[a])
            except:
                print ('[%s]:%s'%(a, dog_dict[a]))
        return obj

    def create_dog_money_flow_class(self, dog_id):
        if dog_id not in self.dog_money_flow_class:
            new_class = type('DogMoneyFlow%s'%(dog_id), (Base, ), dict(
                __tablename__ = 'dog_money_flow_%s'%(dog_id),
                Date = Column(DATETIME, primary_key=True, autoincrement=True),
                CloseValue = Column(Text, nullable=True),
                CloseRate = Column(Text, nullable=True),
                MainIn = Column(Text, nullable=True),
                MainPer = Column(Text, nullable=True),
                BigPlusIn = Column(Text, nullable=True),
                BigPlusPer = Column(Text, nullable=True),
                BigIn = Column(Text, nullable=True),
                BigPer = Column(Text, nullable=True),
                MiddIn = Column(Text, nullable=True),
                MiddPer = Column(Text, nullable=True),
                LittleIn = Column(Text, nullable=True),
                LittlePer = Column(Text, nullable=True),
            ))
            self.dog_money_flow_class.update({dog_id:new_class})
        return self.dog_money_flow_class[dog_id]

    def queryLastDogMoneyFlow(self, dog_id):
        if self.session is None:
            self.connectdb()
        DogMoneyFlow = self.create_dog_money_flow_class(dog_id)
        result = self.session.query(DogMoneyFlow).order_by(sqlalchemy.desc(DogMoneyFlow.Date)).first()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryDogMoneyFlowByDate(self, dog_id, Date):
        if self.session is None:
            self.connectdb()
        DogMoneyFlow = self.create_dog_money_flow_class(dog_id)
        result = self.session.query(DogMoneyFlow).filter(DogMoneyFlow.Date == Date).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def countDogMoneyFlowByDate(self, dog_id, date):
        ret = self.queryDogMoneyFlowByDate(dog_id, date)
        count = 0
        for index in ret:
            count += 1
        return count

    def updateDogMoneyFlowByDate(self, dog_id, date, dog_dict):
        if self.session is None:
            self.connectdb()
        if (self.countDogMoneyFlowByDate(dog_id, date) > 0):
            DogMoneyFlow = self.create_dog_money_flow_class(dog_id)
            self.session.query(DogMoneyFlow).filter(DogMoneyFlow.Date == date).update(dog_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            return self.insertDogMoneyFlow(dog_id, dog_dict)

    def insertDogMoneyFlow(self, dog_id, dog_dict):
        if self.session is None:
            self.connectdb()
        if (self.countDogMoneyFlowByDate(dog_id, dog_dict['Date']) > 0):
            return False
        DogMoneyFlow = self.create_dog_money_flow_class(dog_id)
        dog = DogMoneyFlow()
        dog = self.get_obj_from_dict(dog_dict, dog)
        try:
            self.session.add(dog)
            self.session.commit()
        except:
            return False
        else:
            return True

    def create_money_flow_table(self, table_name):
        meta = MetaData()
        table_name = Table(
            table_name, meta,
            # Primary key
            Column('Date', DATETIME, primary_key=True),
            # Other keys
            Column('CloseValue', Text, nullable=True),
            Column('CloseRate', Text, nullable=True),
            Column('MainIn', Text, nullable=True),
            Column('MainPer', Text, nullable=True),
            Column('BigPlusIn', Text, nullable=True),
            Column('BigPlusPer', Text, nullable=True),
            Column('BigIn', Text, nullable=True),
            Column('BigPer', Text, nullable=True),
            Column('MiddIn', Text, nullable=True),
            Column('MiddPer', Text, nullable=True),
            Column('LittleIn', Text, nullable=True),
            Column('LittlePer', Text, nullable=True),
        )
        meta.create_all(engine)

    def queryTable(self):
        with engine.connect() as conn:
            table_list = []
            result = conn.execute(text("show tables"))
            for index in result:
                table_list.append(index[0])
            return table_list


if __name__ == '__main__':
    db = dogdb()
    db.openSession()

    print (db.countDogByID('001593_Insert_Test'))

    db.deleteDogByID('001593_Insert_Test')
    ret_temp = db.queryDogByID('001593_Insert_Test')
    for index in ret_temp:
        temp_dict = db.get_dict_from_obj(index)
        for member in temp_dict:
            print ('[%s]:%s'%(member, temp_dict[member]))
            pass

    exit()
    '''
    ret = db.queryDogAll()
    for index in ret:
        temp_dict = db.get_dict_from_obj(index)
        for member in temp_dict:
            #print ('[%s]:%s'%(member, temp_dict[member]))
            pass
        obj_temp = db.get_obj_from_dict(temp_dict)
        temp_dict_obj = db.get_dict_from_obj(obj_temp)
        for member in temp_dict_obj:
            #print ('[%s]:%s'%(member, temp_dict_obj[member]))
            pass
    '''

    ret = db.queryDogByID('001593')
    for index in ret:
        temp_dict = db.get_dict_from_obj(index)
        for member in temp_dict:
            #print ('[%s]:%s'%(member, temp_dict[member]))
            pass
        
        '''
        temp_dict.update({'Type':'Modify Test2'})
        db.updateDogSurveyByID(temp_dict['ID'], temp_dict)
        ret_temp = db.queryDogByID('001593')
        for index in ret_temp:
            temp_dict = db.get_dict_from_obj(index)
            for member in temp_dict:
                #print ('[%s]:%s'%(member, temp_dict[member]))
                pass
        '''
        temp_dict.update({'ID':'001593_Insert_Test'})
        flag = db.insertDogSurvey(temp_dict)
        print (flag)
        ret_temp = db.queryDogByID('001593_Insert_Test')
        for index in ret_temp:
            temp_dict = db.get_dict_from_obj(index)
            for member in temp_dict:
                print ('[%s]:%s'%(member, temp_dict[member]))
                pass

    exit()

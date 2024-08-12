#!/bin/python3

# System lib
import os, sys
import time, datetime
from sqlalchemy import MetaData, Table, desc
from sqlalchemy import Column, Integer, String, DATETIME, DATE, Text, VARCHAR, JSON

# Customsized lib
import db_base as dbb

class dogdb(dbb.basedb):
    def create_dog_money_flow_class(self, dog_id):
        table_name = 'dog_money_flow_%s'%(dog_id)
        if table_name not in self.db_class:
            new_class = type('DogMoneyFlow%s'%(dog_id), (self.Base, ), dict(
                __tablename__ = table_name,
                Date = Column(DATETIME, primary_key=True),
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
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

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
        meta.create_all(self.engine)

    def queryDogMoneyFlowAll(self, dog_id):
        if self.session is None:
            self.connectdb()
        DogMoneyFlow = self.create_dog_money_flow_class(dog_id)
        result = self.session.query(DogMoneyFlow).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryLastDogMoneyFlow(self, dog_id):
        if self.session is None:
            self.connectdb()
        DogMoneyFlow = self.create_dog_money_flow_class(dog_id)
        result = self.session.query(DogMoneyFlow).order_by(desc(DogMoneyFlow.Date)).first()
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

################### Dog Money Part End ###############################
################### Dog Money Part Start #############################
    def create_dog_lable_class(self):
        table_name = 'dog_lables'
        if table_name not in self.db_class:
            new_class = type('DogLables', (self.Base, ), dict(
                __tablename__ = table_name,
                ID = Column(String(255), primary_key=True),
                BestAction = Column(JSON, nullable=True),
                Reserve = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

    def create_lable_table(self):
        meta = MetaData()
        table_name = Table(
            'dog_lables', meta,
            # Primary key
            Column('ID', String(255), primary_key=True),
            # Other keys
            Column('BestAction', JSON, nullable=True),
            Column('Reserve', Text, nullable=True),
        )
        meta.create_all(self.engine)

    def queryDogLablesAll(self):
        if self.session is None:
            self.connectdb()
        DogLables = self.create_dog_lable_class()
        result = self.session.query(DogLables).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryDogLablesById(self, dog_id):
        if self.session is None:
            self.connectdb()
        DogLables = self.create_dog_lable_class()
        result = self.session.query(DogLables).filter(DogLables.ID == dog_id).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def countDogLablesById(self, dog_id):
        ret = self.queryDogLablesById(dog_id)
        count = 0
        for index in ret:
            count += 1
        return count

    def updateDogLablesByID(self, dog_id, dog_lables_dict):
        if self.session is None:
            self.connectdb()
        if (self.countDogLablesById(dog_id) == 1):
            DogLables = self.create_dog_lable_class()
            self.session.query(DogLables).filter(DogLables.id == dog_id).update(dog_lables_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            return self.insertDogLables(dog_id, dog_lables_dict)

    def insertDogLables(self, dog_id, dog_lables_dict):
        if self.session is None:
            self.connectdb()
        if (self.countDogLablesById(dog_id) == 1):
            return False
        DogLables = self.create_dog_lable_class()
        dog = DogLables()
        dog = self.get_obj_from_dict(dog_lables_dict, dog)
        try:
            self.session.add(dog)
            self.session.commit()
        except:
            return False
        else:
            return True

################### Dog Lables Part End ###############################

#!/bin/python3

# System lib
import os, sys
import time, datetime
from sqlalchemy import MetaData, Table, desc
from sqlalchemy import Column, Integer, String, DATETIME, DATE, Text, VARCHAR, JSON, FLOAT

# Customsized lib
import db_base as dbb

class db(dbb.basedb):

    def create_realtime_param_class(self):
        table_name = 'realtime_parameters'
        if table_name not in self.db_class:
            new_class = type(table_name, (self.Base, ), dict(
                __tablename__ = table_name,
                Symbol = Column(String(255), primary_key=True),
                Content = Column(JSON, nullable=True),
                Reserved = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

    def create_realtime_param_table(self):
        meta = MetaData()
        tmp = Table(
            'realtime_parameters', meta,
            # Primary key
            Column('Symbol', String(255), primary_key=True),
            # Other keys
            Column('Content', JSON, nullable=True),
            Column('Reserved', Text, nullable=True),
        )
        meta.create_all(self.engine)

    def is_param_table_exist(self):
        tables = self.queryTable()
        if ('realtime_parameters' not in tables):
            return False
        return True

    def is_param_exist(self, symbol):
        ret = self.query_param_by_symbol(symbol)
        if len(ret) > 0:
            return True
        return False

    def query_param_by_symbol(self, symbol):
        if self.session is None:
            self.connectdb()
        Cls = self.create_realtime_param_class()
        result = self.session.query(Cls).filter(Cls.Symbol == symbol).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def insert_param(self, param_dict):
        if self.session is None:
            self.connectdb()
        Cls = self.create_realtime_param_class()
        obj = Cls()
        obj = self.get_obj_from_dict(param_dict, obj)
        try:
            self.session.add(obj)
            self.session.commit()
        except:
            return False
        else:
            return False

    def update_param_by_symbol(self, symbol, param_dict):
        if self.session is None:
            self.connectdb()
        if (self.is_param_exist(symbol)):
            Cls = self.create_realtime_param_class()
            self.session.query(Cls).filter(Cls.Symbol == symbol).update(param_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            return self.insert_param(param_dict)

######################## Div ########################

    def create_realtime_dog_class(self):
        table_name = 'realtime_dog'
        if table_name not in self.db_class:
            new_class = type(table_name, (self.Base, ), dict(
                __tablename__ = table_name,
                DogTime = Column(String(255), primary_key=True),
                Price = Column(FLOAT, nullable=True),
                Close = Column(FLOAT, nullable=True),
                High = Column(FLOAT, nullable=True),
                Low = Column(FLOAT, nullable=True),
                Volume = Column(Integer, nullable=True),
                Turnover = Column(FLOAT, nullable=True),
                Capital = Column(JSON, nullable=True),
                Reserved = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

    def create_realtime_dog_table(self):
        meta = MetaData()
        tmp = Table(
            'realtime_dog', meta,
            # Primary key
            Column('DogTime', String(255), primary_key=True),
            # Other keys
            Column('Price', FLOAT, nullable=True),
            Column('Close', FLOAT, nullable=True),
            Column('High', FLOAT, nullable=True),
            Column('Low', FLOAT, nullable=True),
            Column('Volume', Integer, nullable=True),
            Column('Turnover', FLOAT, nullable=True),
            Column('Capital', JSON, nullable=True),
            Column('Reserved', Text, nullable=True),
        )
        meta.create_all(self.engine)

    def is_dog_table_exist(self):
        tables = self.queryTable()
        if ('realtime_dog' not in tables):
            return False
        return True

    def is_dog_exist(self, dog_time):
        ret = self.query_sharing_by_dogtime(dog_time)
        if len(ret) > 0:
            return True
        return False

    def query_sharing_by_dogtime(self, dog_time):
        if self.session is None:
            self.connectdb()
        Cls = self.create_realtime_dog_class()
        result = self.session.query(Cls).filter(Cls.DogTime == dog_time).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def query_sharing_by_dog(self, dog_id):
        if self.session is None:
            self.connectdb()
        Cls = self.create_realtime_dog_class()
        result = self.session.query(Cls).filter(Cls.DogTime.like('{0}-%'.format(dog_id))).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def insert_sharing(self, sharing_dict):
        if self.session is None:
            self.connectdb()
        Cls = self.create_realtime_dog_class()
        obj = Cls()
        obj = self.get_obj_from_dict(sharing_dict, obj)
        try:
            self.session.add(obj)
            self.session.commit()
        except:
            return False
        else:
            return True

    def update_sharing_by_dogtime(self, dog_time, sharing_dict):
        if self.session is None:
            self.connectdb()
        if (self.is_dog_exist(dog_time)):
            Cls = self.create_realtime_dog_class()
            self.session.query(Cls).filter(Cls.DogTime == dog_time).update(sharing_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            return self.insert_sharing(sharing_dict)

    def del_sharing_by_dogtime(self, dog_time):
        if self.session is None:
            self.connectdb()
        Cls = self.create_realtime_dog_class()
        obj = Cls()
        obj = self.session.query(Cls).filter(Cls.DogTime == dog_time).first()
        try:
            self.session.delete(obj)
            self.session.commit()
        except:
            return False
        else:
            return True
        

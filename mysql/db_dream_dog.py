#!/bin/python3

# System lib
import os, sys
import time, datetime
from sqlalchemy import MetaData, Table, desc
from sqlalchemy import Column, Integer, String, DATETIME, DATE, Text, VARCHAR, JSON

# Customsized lib
import db_base as dbb

class db(dbb.basedb):

############# Dog Market Start ########################
    def create_dog_market_class(self, dog_id):
        table_name = 'dog_market_%s'%(dog_id)
        if table_name not in self.db_class:
            new_class = type(table_name, (self.Base, ), dict(
                __tablename__ = table_name,
                Date = Column(DATE, primary_key=True),
                Open = Column(Text, nullable=True),
                Close = Column(Text, nullable=True),
                High = Column(Text, nullable=True),
                Low = Column(Text, nullable=True),
                Amount = Column(Text, nullable=True),
                Inflow_Main = Column(Text, nullable=True),
                Inflow_Max = Column(Text, nullable=True),
                Inflow_Lg = Column(Text, nullable=True),
                Inflow_Mid = Column(Text, nullable=True),
                Inflow_Sm = Column(Text, nullable=True),
                Reserved = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

    def create_dog_market_table(self, dog_id):
        meta = MetaData()
        tmp = Table(
            'dog_market_%s'%(dog_id), meta,
            # Primary key
            Column('Date', DATE, primary_key=True),
            # Other keys
            Column('Open', Text, nullable=True),
            Column('Close', Text, nullable=True),
            Column('High', Text, nullable=True),
            Column('Low', Text, nullable=True),
            Column('Amount', Text, nullable=True),
            Column('Inflow_Main', Text, nullable=True),
            Column('Inflow_Max', Text, nullable=True),
            Column('Inflow_Lg', Text, nullable=True),
            Column('Inflow_Mid', Text, nullable=True),
            Column('Inflow_Sm', Text, nullable=True),
            Column('Reserved', Text, nullable=True),
        )
        meta.create_all(self.engine)

    def is_table_exist(self, dog_id):
        tables = self.queryTable()
        if ('dog_market_%s'%(dog_id) not in tables):
            return False
        return True

    def is_date_exist(self, dog_id, date):
        ret = self.query_dog_markey_by_date(dog_id, date)
        if len(ret) > 0:
            return True
        return False

    def query_dog_markey_all(self, dog_id):
        if self.session is None:
            self.connectdb()
        dog_market = self.create_dog_market_class(dog_id)
        result = self.session.query(dog_market).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def query_dog_market_last(self, dog_id):
        if self.session is None:
            self.connectdb()
        dog_market = self.create_dog_market_class(dog_id)
        result = self.session.query(dog_market).order_by(desc(dog_market.Date)).first()
        try:
            self.session.commit()
        except:
            return None
        else:
            return result

    def query_dog_markey_by_date(self, dog_id, date):
        if self.session is None:
            self.connectdb()
        dog_market = self.create_dog_market_class(dog_id)
        result = self.session.query(dog_market).filter(dog_market.Date == date).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def query_dog_markey_by_daterange(self, dog_id, start, end):
        if self.session is None:
            self.connectdb()
        dog_market = self.create_dog_market_class(dog_id)
        result = self.session.query(dog_market).filter(dog_market.Date.between(start, end)).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def update_dog_market_by_date(self, dog_id, date, dog_dict):
        if self.session is None:
            self.connectdb()
        if (self.is_date_exist(dog_id, date)):
            dog_market = self.create_dog_market_class(dog_id)
            self.session.query(dog_market).filter(dog_market.Date == date).update(dog_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            return self.insert_dog_market(dog_id, dog_dict)

    def insert_dog_market(self, dog_id, dog_dict):
        if self.session is None:
            self.connectdb()
        if (self.is_date_exist(dog_id, dog_dict['Date'])):      # Skip if exist
            return True
        dog_market = self.create_dog_market_class(dog_id)
        dog = dog_market()
        dog = self.get_obj_from_dict(dog_dict, dog)
        try:
            self.session.add(dog)
            self.session.commit()
        except:
            return False
        else:
            return True
############# Dog Market End ########################
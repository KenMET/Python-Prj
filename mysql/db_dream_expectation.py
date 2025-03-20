#!/bin/python3

# System lib
import os, sys
import time, datetime
from sqlalchemy import MetaData, Table, desc
from sqlalchemy import Column, Integer, String, DATE, Text

# Customsized lib
import db_base as dbb

class db(dbb.basedb):

############# Expectation Start ########################
    def create_expectation_class(self):
        table_name = 'dog_expectation'
        if table_name not in self.db_class:
            new_class = type(table_name, (self.Base, ), dict(
                __tablename__ = table_name,
                Date = Column(DATE, primary_key=True),
                Us_Expectation = Column(Text, nullable=True),
                Cn_Expectation = Column(Text, nullable=True),
                Reserved = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

    def create_expectation_table(self):
        meta = MetaData()
        tmp = Table(
            'dog_expectation', meta,
            # Primary key
            Column('Date', DATE, primary_key=True),
            # Other keys
            Column('Us_Expectation', Text, nullable=True),
            Column('Cn_Expectation', Text, nullable=True),
            Column('Reserved', Text, nullable=True),
        )
        meta.create_all(self.engine)

    def is_table_exist(self):
        tables = self.queryTable()
        if ('dog_expectation'):
            return False
        return True

    def is_date_exist(self, date):
        ret = self.query_expectation_by_date(date)
        if len(ret) > 0:
            return True
        return False

    def query_expectation_by_date(self, date):
        if self.session is None:
            self.connectdb()
        Expectation = self.create_expectation_class()
        result = self.session.query(Expectation).filter(Expectation.Date == date).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def get_latest_expectation(self, offset=0):
        if self.session is None:
            self.connectdb()
        Expectation = self.create_expectation_class()
        
        result = self.session.query(Expectation).order_by(Expectation.Date.desc()).offset(offset).first()
        try:
            self.session.commit()
        except:
            return None
        else:
            return result

    def update_expectation_by_date(self, date, expectation_dict):
        if self.session is None:
            self.connectdb()
        if (self.is_date_exist(date)):
            Expectation = self.create_expectation_class()
            self.session.query(Expectation).filter(Expectation.Date == date).update(expectation_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            return self.insert_expectation(expectation_dict)

    def insert_expectation(self, expectation_dict):
        if self.session is None:
            self.connectdb()
        if (self.is_date_exist(expectation_dict['Date'])):      # Skip if exist
            return True
        Expectation = self.create_expectation_class()
        expectation = Expectation()
        expectation = self.get_obj_from_dict(expectation_dict, expectation)
        try:
            self.session.add(expectation)
            self.session.commit()
        except:
            return False
        else:
            return True
############# Expectation End ########################
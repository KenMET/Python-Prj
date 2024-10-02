#!/bin/python3

# System lib
import os, sys
import time, datetime
from sqlalchemy import MetaData, Table, desc
from sqlalchemy import Column, Integer, String, DATETIME, DATE, Text, VARCHAR, JSON

# Customsized lib
import db_base as dbb

class db(dbb.basedb):
                 
############# Dog Info US Start ########################
    def create_dog_us_info_class(self):
        table_name = 'dog_us_info'
        if table_name not in self.db_class:
            new_class = type(table_name, (self.Base, ), dict(
                __tablename__ = table_name,
                Code = Column(String(255), primary_key=True),
                Name = Column(Text, nullable=True),
                Last_Price = Column(Text, nullable=True),
                Total_Value = Column(Text, nullable=True),
                PE_ratio = Column(Text, nullable=True),
                Turnover_Rate = Column(Text, nullable=True),
                Reserved = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

    def create_dog_us_info_table(self):
        meta = MetaData()
        tmp = Table(
            'dog_us_info', meta,
            # Primary key
            Column('Code', String(255), primary_key=True),
            # Other keys
            Column('Name', Text, nullable=True),
            Column('Last_Price', Text, nullable=True),
            Column('Total_Value', Text, nullable=True),
            Column('PE_ratio', Text, nullable=True),
            Column('Turnover_Rate', Text, nullable=True),
            Column('Reserved', Text, nullable=True),
        )
        meta.create_all(self.engine)

    def is_table_exist(self):
        tables = self.queryTable()
        if ('dog_us_info' not in tables):
            return False
        return True

    def delete_dog_us_all(self):
        if self.session is None:
            self.connectdb()
        dog_info = self.create_dog_us_info_class()
        result = self.session.query(dog_info).delete() 
        try:
            self.session.commit()
        except:
            return False
        else:
            return True

    def query_dog_fullcode_by_code(self, dog_code):
        if self.session is None:
            self.connectdb()
        dog_info = self.create_dog_us_info_class()
        result = self.session.query(dog_info).filter(dog_info.Code.like('%{0}%'.format(dog_code))).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def insert_dog_us(self, dog_us_dict):
        if self.session is None:
            self.connectdb()
        DogUS = self.create_dog_us_info_class()
        new = DogUS()
        new = self.get_obj_from_dict(dog_us_dict, new)
        if new == None:
            return False
        try:
            self.session.add(new)
            self.session.commit()
        except:
            return False
        else:
            return True
############# Dog Info US End ########################
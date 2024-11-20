#!/bin/python3

# System lib
import os, sys
import time, datetime
from sqlalchemy import MetaData, Table, desc
from sqlalchemy import Column, Integer, String, DATETIME, DATE, Text, VARCHAR, JSON

# Customsized lib
import db_base as dbb

class db(dbb.basedb):

############# Dog Option Start ########################
    def create_dog_option_class(self):
        table_name = 'dog_option'
        if table_name not in self.db_class:
            new_class = type(table_name, (self.Base, ), dict(
                __tablename__ = table_name,
                CodeDatePrice = Column(String(255), primary_key=True),
                CallSymbol = Column(Text, nullable=True),
                CallSymbolPrice = Column(Text, nullable=True),
                PutSymbol = Column(Text, nullable=True),
                PutSymbolPrice = Column(Text, nullable=True),
                Standard = Column(Text, nullable=True),
                Reserved = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

    def create_dog_option_table(self):
        meta = MetaData()
        tmp = Table(
            'dog_option', meta,
            # Primary key
            Column('CodeDatePrice', String(255), primary_key=True),
            # Other keys
            Column('CallSymbol', Text, nullable=True),
            Column('CallSymbolPrice', Text, nullable=True),
            Column('PutSymbol', Text, nullable=True),
            Column('PutSymbolPrice', Text, nullable=True),
            Column('Standard', Text, nullable=True),
            Column('Reserved', Text, nullable=True),
        )
        meta.create_all(self.engine)

    def is_table_exist(self):
        tables = self.queryTable()
        if ('dog_option' not in tables):
            return False
        return True

    def query_dog_option_by_id(self, dog_id):
        if self.session is None:
            self.connectdb()
        dog_option = self.create_dog_option_class(dog_id)
        result = self.session.query(dog_option).filter(dog_info.Code.like('%{0}%'.format(dog_id))).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def insert_dog_option(self, dog_id, dog_dict):
        if self.session is None:
            self.connectdb()
        if (self.is_date_exist(dog_id, dog_dict['Date'])):      # Skip if exist
            return True
        dog_option = self.create_dog_option_class(dog_id)
        dog = dog_option()
        dog = self.get_obj_from_dict(dog_dict, dog)
        try:
            self.session.add(dog)
            self.session.commit()
        except:
            return False
        else:
            return True
############# Dog Option End ########################
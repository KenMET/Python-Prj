#!/bin/python3

# System lib
import os, sys
import time, datetime
from sqlalchemy import MetaData, Table, desc, and_
from sqlalchemy import Column, Integer, String, DATETIME, DATE, Text, VARCHAR, JSON

# Customsized lib
import db_base as dbb

class db(dbb.basedb):
    def create_secret_class(self):
        table_name = 'secret'
        if table_name not in self.db_class:
            new_class = type(table_name, (self.Base, ), dict(
                __tablename__ = table_name,
                Type = Column(String(255), primary_key=True),
                App_Key = Column(Text, nullable=True),
                App_Secret = Column(Text, nullable=True),
                Access_Token = Column(Text, nullable=True),
                Reserved = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

    def create_secret_table(self):
        meta = MetaData()
        temp = Table(
            'secret', meta,
            # Primary key
            Column('Type', String(255), primary_key=True),
            # Other keys
            Column('App_Key', Text, nullable=True),
            Column('App_Secret', Text, nullable=True),
            Column('Access_Token', Text, nullable=True),
            Column('Reserved', Text, nullable=True),
        )
        meta.create_all(self.engine)

    def is_table_exist(self):
        tables = self.queryTable()
        if ('secret' not in tables):
            return False
        return True

    def query_all_secret(self):
        if self.session is None:
            self.connectdb()
        query_class = self.create_secret_class()
        result = self.session.query(query_class).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def query_secret_by_type(self, quant_type, user):
        if self.session is None:
            self.connectdb()
        query_class = self.create_secret_class()
        full = '%s-%s'%(user, quant_type)
        result = self.session.query(query_class).filter(query_class.Type == full).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def insert_secret(self, user_dict):
        if self.session is None:
            self.connectdb()
        Secret = self.create_secret_class()
        new = Secret()
        new = self.get_obj_from_dict(user_dict, new)
        if new == None:
            return False
        try:
            self.session.add(new)
            self.session.commit()
        except:
            return False
        else:
            return True

    def update_secret(self, user_dict):
        if self.session is None:
            self.connectdb()
        user_type = user_dict['Type']
        user = user_type.split('-')[0]
        q_type = user_type.split('-')[1]
        if (len(self.query_secret_by_type(q_type, user)) > 0):
            Secret = self.create_secret_class()
            self.session.query(Secret).filter(Secret.Type == user_type).update(user_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            return self.insert_secret(user_dict)

#!/bin/python3

# System lib
import os, sys
import time, datetime
from sqlalchemy import MetaData, Table, desc
from sqlalchemy import Column, Integer, String, DATETIME, DATE, Text, VARCHAR, JSON

# Customsized lib
import db_base as dbb

class db(dbb.basedb):
                 
############# Dog House Start ########################
    def create_house_class(self):
        table_name = 'house'
        if table_name not in self.db_class:
            new_class = type(table_name, (self.Base, ), dict(
                __tablename__ = table_name,
                Account = Column(String(255), primary_key=True),
                NetAssets = Column(Text, nullable=True),
                TotalCash = Column(Text, nullable=True),
                MaxFinanceAmount = Column(Text, nullable=True),
                RiskLevel = Column(Text, nullable=True),
                BuyPower = Column(Text, nullable=True),
                FrozenCash = Column(Text, nullable=True),
                SettlingCash = Column(Text, nullable=True),
                AvailableCash = Column(Text, nullable=True),
                WithdrawCash = Column(Text, nullable=True),
                Holding = Column(Text, nullable=True),
                Reserved = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

    def create_house_table(self):
        meta = MetaData()
        tmp = Table(
            'house', meta,
            # Primary key
            Column('Account', String(255), primary_key=True),
            # Other keys
            Column('NetAssets', Text, nullable=True),
            Column('TotalCash', Text, nullable=True),
            Column('MaxFinanceAmount', Text, nullable=True),
            Column('RiskLevel', Text, nullable=True),
            Column('BuyPower', Text, nullable=True),
            Column('FrozenCash', Text, nullable=True),
            Column('SettlingCash', Text, nullable=True),
            Column('AvailableCash', Text, nullable=True),
            Column('WithdrawCash', Text, nullable=True),
            Column('Holding', Text, nullable=True),
            Column('Reserved', Text, nullable=True),
        )
        meta.create_all(self.engine)

    def is_table_exist(self):
        tables = self.queryTable()
        if ('house' not in tables):
            return False
        return True

    def delete_house_all(self):
        if self.session is None:
            self.connectdb()
        house_info = self.create_house_class()
        result = self.session.query(house_info).delete() 
        try:
            self.session.commit()
        except:
            return False
        else:
            return True

    def query_house_by_name(self, name):
        if self.session is None:
            self.connectdb()
        house_info = self.create_house_class()
        result = self.session.query(house_info).filter(house_info.Account == name).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def is_house_exist(self, name):
        temp = self.query_house_by_name(name)
        if len(temp) != 0:
            return True
        return False

    def insert_house(self, house_dict):
        if self.session is None:
            self.connectdb()
        House = self.create_house_class()
        new = House()
        new = self.get_obj_from_dict(house_dict, new)
        if new == None:
            return False
        try:
            self.session.add(new)
            self.session.commit()
        except:
            return False
        else:
            return True
    
    def update_house_by_name(self, name, house_dict):
        if self.session is None:
            self.connectdb()
        if (self.is_house_exist(name)):
            House = self.create_house_class()
            self.session.query(House).filter(House.Account == name).update(house_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            return self.insert_house(house_dict)
############# Dog Info US End ########################
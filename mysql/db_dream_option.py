#!/bin/python3

# System lib
import os, sys
import time, datetime
from sqlalchemy import MetaData, Table, desc
from sqlalchemy import Column, Integer, String, DATETIME, DATE, Text, VARCHAR, JSON, FLOAT

# Customsized lib
import db_base as dbb

class db(dbb.basedb):

############# Dog Option Start ########################
    def create_dog_option_class(self):
        table_name = 'dog_option'
        if table_name not in self.db_class:
            new_class = type(table_name, (self.Base, ), dict(
                __tablename__ = table_name,
                Symbol = Column(String(255), primary_key=True),
                Price = Column(FLOAT, nullable=True),
                Close = Column(FLOAT, nullable=True),
                Open = Column(FLOAT, nullable=True),
                High = Column(FLOAT, nullable=True),
                Low = Column(FLOAT, nullable=True),
                LastUpdate = Column(DATETIME, nullable=True),
                LastVolume = Column(Integer, nullable=True),
                LastTurnover = Column(FLOAT, nullable=True),
                TradeStatus = Column(Text, nullable=True),
                ImpliedVolatility = Column(FLOAT, nullable=True),
                OpenInterest = Column(Integer, nullable=True),
                StrikePrice = Column(FLOAT, nullable=True),
                ContractMultiplier = Column(Integer, nullable=True),
                ContractType = Column(Text, nullable=True),
                HistoricalVolatility = Column(FLOAT, nullable=True),
                Reserved = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

    def create_dog_option_table(self):
        meta = MetaData()
        tmp = Table(
            'dog_option', meta,
            # Primary key
            Column('Symbol', String(255), primary_key=True),
            # Other keys
            Column('Price', FLOAT, nullable=True),
            Column('Close', FLOAT, nullable=True),
            Column('Open', FLOAT, nullable=True),
            Column('High', FLOAT, nullable=True),
            Column('Low', FLOAT, nullable=True),
            Column('LastUpdate', DATETIME, nullable=True),
            Column('LastVolume', Integer, nullable=True),
            Column('LastTurnover', FLOAT, nullable=True),
            Column('TradeStatus', Text, nullable=True),
            Column('ImpliedVolatility', FLOAT, nullable=True),
            Column('OpenInterest', Integer, nullable=True),
            Column('StrikePrice', FLOAT, nullable=True),
            Column('ContractMultiplier', Integer, nullable=True),
            Column('ContractType', Text, nullable=True),
            Column('HistoricalVolatility', FLOAT, nullable=True),
            Column('Reserved', Text, nullable=True),
        )
        meta.create_all(self.engine)

    def is_table_exist(self):
        tables = self.queryTable()
        if ('dog_option' not in tables):
            return False
        return True

    def is_option_exist(self, symbol):
        ret = self.query_option_by_symbol(symbol)
        if len(ret) > 0:
            return True
        return False

    def query_option_by_symbol(self, symbol):
        if self.session is None:
            self.connectdb()
        dog_option = self.create_dog_option_class()
        result = self.session.query(dog_option).filter(dog_option.Symbol == symbol).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def query_option_by_dog(self, dog_id, direction):
        if self.session is None:
            self.connectdb()
        dog_option = self.create_dog_option_class()
        result = self.session.query(dog_option).filter(dog_option.Symbol.like('{0}%{1}%'.format(dog_id, direction))).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def insert_dog_option(self, dog_dict):
        if self.session is None:
            self.connectdb()
        dog_option = self.create_dog_option_class()
        option = dog_option()
        option = self.get_obj_from_dict(dog_dict, option)
        try:
            self.session.add(option)
            self.session.commit()
        except:
            return False
        else:
            return True

    def update_option_by_symbol(self, symbol, option_dict):
        if self.session is None:
            self.connectdb()
        if (self.is_option_exist(symbol)):
            dog_option = self.create_dog_option_class()
            self.session.query(dog_option).filter(dog_option.Symbol == symbol).update(option_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            return self.insert_dog_option(option_dict)

############# Dog Option End ########################
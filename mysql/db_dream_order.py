#!/bin/python3

# System lib
import os, sys
import time, datetime
from sqlalchemy import MetaData, Table, desc, and_
from sqlalchemy import Column, Integer, String, DATETIME, DATE, Text, VARCHAR, JSON

# Customsized lib
import db_base as dbb

class db(dbb.basedb):

############# Dog Order Start ########################
    def create_order_class(self, order_dest):
        table_name = 'order_%s'%(order_dest)
        if table_name not in self.db_class:
            new_class = type(table_name, (self.Base, ), dict(
                __tablename__ = table_name,
                OrderID = Column(String(64), primary_key=True),
                Date = Column(DATETIME, nullable=True),
                Side = Column(Text, nullable=True),
                Type = Column(Text, nullable=True),
                Code = Column(Text, nullable=True),
                Currency = Column(Text, nullable=True),
                Quantity = Column(Text, nullable=True),         # x/y, x=Actual transaction, y=Submitted transaction
                Price = Column(Text, nullable=True),            # Submitted Price
                ExecutedPrice = Column(Text, nullable=True),    # Actual Executed Price
                Fee = Column(Text, nullable=True),
                Status = Column(Text, nullable=True),
                Reserved = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

    def create_order_table(self, order_dest):
        meta = MetaData()
        tmp = Table(
            'order_%s'%(order_dest), meta,
            # Primary key
            Column('OrderID', String(64), primary_key=True),
            # Other keys
            Column('Date', DATETIME, nullable=True),
            Column('Side', Text, nullable=True),
            Column('Type', Text, nullable=True),
            Column('Code', Text, nullable=True),
            Column('Currency', Text, nullable=True),
            Column('Quantity', Text, nullable=True),
            Column('Price', Text, nullable=True),
            Column('ExecutedPrice', Text, nullable=True),
            Column('Fee', Text, nullable=True),
            Column('Status', Text, nullable=True),
            Column('Reserved', Text, nullable=True),
        )
        meta.create_all(self.engine)

    def is_table_exist(self, order_dest):
        tables = self.queryTable()
        if ('order_%s'%(order_dest) not in tables):
            return False
        return True

    def is_order_exist(self, order_dest, order_id):
        ret = self.query_order_by_id(order_dest, order_id)
        if len(ret) > 0:
            return True
        return False

    def query_order_by_id(self, order_dest, order_id):
        if self.session is None:
            self.connectdb()
        dog_order = self.create_order_class(order_dest)
        result = self.session.query(dog_order).filter(dog_order.OrderID == order_id).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def query_order_opened(self, order_dest):
        if self.session is None:
            self.connectdb()
        dog_order = self.create_order_class(order_dest)
        conditions = and_(dog_order.Status != 'Canceled', dog_order.Status != 'Expired')
        result = self.session.query(dog_order).filter(conditions).all()
        #result = self.session.query(dog_order).filter(dog_order.Status != 'Canceled').all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def insert_order(self, order_dest, order_dict):
        if self.session is None:
            self.connectdb()
        if (self.is_order_exist(order_dest, order_dict['OrderID'])):      # Skip if exist
            return True
        dog_order = self.create_order_class(order_dest)
        order = dog_order()
        order = self.get_obj_from_dict(order_dict, order)
        try:
            self.session.add(order)
            self.session.commit()
        except:
            return False
        else:
            return True

    def update_order_by_id(self, order_dest, order_id, order_dict):
        if self.session is None:
            self.connectdb()
        if (self.is_order_exist(order_dest, order_id)):
            dog_order = self.create_order_class(order_dest)
            self.session.query(dog_order).filter(dog_order.OrderID == order_id).update(order_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            return self.insert_order(order_dest, order_dict)


############# Dog Order End ########################
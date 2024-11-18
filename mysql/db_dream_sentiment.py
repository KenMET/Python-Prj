#!/bin/python3

# System lib
import os, sys
import time, datetime
from sqlalchemy import MetaData, Table, desc, and_
from sqlalchemy import Column, Integer, String, DATETIME, DATE, Text, VARCHAR, JSON

# Customsized lib
import db_base as dbb

class db(dbb.basedb):
############# Sentiment Start ########################
    def create_sentiment_class(self):
        table_name = 'sentiment'
        if table_name not in self.db_class:
            new_class = type(table_name, (self.Base, ), dict(
                __tablename__ = table_name,
                Title = Column(String(512), primary_key=True),
                PublishTime = Column(DATETIME, nullable=True),
                Code = Column(Text, nullable=True),
                Score = Column(Text, nullable=True),
                Summary = Column(Text, nullable=True),
                Reserved = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

    def create_sentiment_table(self):
        meta = MetaData()
        tmp = Table(
            'sentiment', meta,
            # Primary key
            Column('Title', String(512), primary_key=True),
            # Other keys
            Column('PublishTime', DATETIME, nullable=True),
            Column('Code', Text, nullable=True),
            Column('Score', Text, nullable=True),
            Column('Summary', Text, nullable=True),
            Column('Reserved', Text, nullable=True),
        )
        meta.create_all(self.engine)

    def is_table_exist(self):
        tables = self.queryTable()
        if ('sentiment' not in tables):
            return False
        return True

    def query_sentiment_by_id(self, id):
        if self.session is None:
            self.connectdb()
        sentiment_info = self.create_sentiment_class()
        result = self.session.query(sentiment_info).filter(sentiment_info.Code == id).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result
    
    def query_sentiment_by_id_date(self, id, start, end):
        if self.session is None:
            self.connectdb()
        sentiment_info = self.create_sentiment_class()
        result = self.session.query(sentiment_info).filter(and_(
            sentiment_info.Code.like(id),
            sentiment_info.PublishTime >= start,
            sentiment_info.PublishTime <= end
        )).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def is_sentiment_exist(self, name):
        temp = self.query_sentiment_by_name(name)
        if len(name) != 0:
            return True
        return False

    def insert_sentiment(self, sentiment_dict):
        if self.session is None:
            self.connectdb()
        Sentiment = self.create_sentiment_class()
        new = Sentiment()
        new = self.get_obj_from_dict(sentiment_dict, new)
        if new == None:
            return False
        try:
            self.session.add(new)
            self.session.commit()
        except:
            return False
        else:
            return True
    
    # Not allow to update sentiment.
    def update_sentiment_by_name(self, name, sentiment_dict):
        pass
############# Sentiment End ########################
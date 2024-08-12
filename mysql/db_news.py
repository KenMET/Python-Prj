#!/bin/python3

# System lib
import os, sys
import time, datetime
from sqlalchemy import MetaData, Table, desc
from sqlalchemy import Column, Integer, String, DATETIME, DATE, Text, VARCHAR, JSON

# Customsized lib
import db_base as dbb

class newsdb(dbb.basedb):
    def create_top_news_class(self):
        table_name = 'top_news'
        if table_name not in self.db_class:
            new_class = type('NewsTop', (self.Base, ), dict(
                __tablename__ = table_name,
                Title = Column(String(255), primary_key=True),
                Type = Column(Text, nullable=True),
                Time = Column(DATETIME, nullable=True),
                Url = Column(Text, nullable=True),
                ChannelUrl = Column(Text, nullable=True),
                ImpactArea = Column(Text, nullable=True),
                Lables = Column(Text, nullable=True),
                OriginContent = Column(Text, nullable=True),
                Reserve = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

    def create_top_news_table(self):
        meta = MetaData()
        table_name = Table(
            'top_news', meta,
            # Primary key
            Column('Title', String(255), primary_key=True),
            # Other keys
            Column('Type', Text, nullable=True),
            Column('Time', DATETIME, nullable=True),
            Column('Url', Text, nullable=True),
            Column('ChannelUrl', Text, nullable=True),
            Column('ImpactArea', Text, nullable=True),
            Column('Lables', Text, nullable=True),
            Column('OriginContent', Text, nullable=True),
            Column('Reserve', Text, nullable=True),
        )
        meta.create_all(self.engine)

    def queryTopNewsAll(self):
        if self.session is None:
            self.connectdb()
        NewsTop = self.create_top_news_class()
        result = self.session.query(NewsTop).all() 
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryTopNewsByTitle(self, Title):
        if self.session is None:
            self.connectdb()
        NewsTop = self.create_top_news_class()
        result = self.session.query(NewsTop).filter(NewsTop.Title == Title).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryTopNewsByTitleSimilar(self, similar_title):
        if self.session is None:
            self.connectdb()
        NewsTop = self.create_top_news_class()
        result = self.session.query(NewsTop).filter(NewsTop.Title.like('%{0}%'.format(similar_title))).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryTopNewsNoneContent(self):
        if self.session is None:
            self.connectdb()
        NewsTop = self.create_top_news_class()
        result = self.session.query(NewsTop).filter(NewsTop.OriginContent == None).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryLastNew(self):
        if self.session is None:
            self.connectdb()
        NewsTop = self.create_top_news_class()
        result = self.session.query(NewsTop).order_by(desc(NewsTop.Time)).first()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def insertTopNews(self, news_dict):
        if self.session is None:
            self.connectdb()
        NewsTop = self.create_top_news_class()
        query_temp = self.queryTopNewsByTitle(news_dict['Title'])
        if (len(query_temp) == 1):
            query_dict = self.get_dict_from_obj(query_temp[0])
            if (str(query_dict['Time']) < (news_dict['Time']+':00')):    # update to latest data
                self.session.query(NewsTop).filter(NewsTop.Title == news_dict['Title']).update(news_dict)
                return True
            return False
        elif (len(query_temp) > 1):      # May not enter this section, Just return a None to raise a fatal
            return None
        new = NewsTop()
        new = self.get_obj_from_dict(news_dict, new)
        if new == None:
            return False
        try:
            self.session.add(new)
            self.session.commit()
        except:
            return False
        else:
            return True

    def deleteNewsByTitle(self, title):
        if self.session is None:
            self.connectdb()
        if title is None or len(title.strip()) == 0:
            return None
        NewsTop = self.create_top_news_class()
        result = self.session.query(NewsTop).filter(NewsTop.Title == title).delete(synchronize_session=False) 
        self.session.flush()
        try:
            self.session.commit()
        except:
            return False
        else:
            return True

'''
    def queryNewsByDate(self, date):
        if self.session is None:
            self.connectdb()
        NewsTop = self.create_top_news_class()
        result = self.session.query(NewsTop).filter(NewsTop.NetValueTime == date).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def updateTopNewsByName(self, Name, news_dict):
        if self.session is None:
            self.connectdb()
        if (self.countCatByID(ID) > 0):
            CatSurvey = self.create_top_news_class()
            self.session.query(CatSurvey).filter(CatSurvey.ID == ID).update(news_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            cat_dict.update({'ID':ID})
            return self.insertCatSurvey(cat_dict)

    def insertTopNews(self, cat_dict):
        if self.session is None:
            self.connectdb()
        if (self.countCatByID(cat_dict['ID']) > 0):
            return False
        CatSurvey = self.create_cat_survey_class()
        cat = CatSurvey()
        cat = self.get_obj_from_dict(cat_dict, cat)
        if cat == None:
            return False
        try:
            self.session.add(cat)
            self.session.commit()
        except:
            return False
        else:
            return True

'''
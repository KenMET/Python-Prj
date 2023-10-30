import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DATETIME, Text, VARCHAR, DATE
from sqlalchemy.orm import sessionmaker, relationship
import pymysql
import datetime
from pathlib import Path
import os
import time

HOSTNAME = os.environ['HOSTNAME']
DATABASE = 'kanos_news'
PORT = int(os.environ['PORT'])
USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']
DB_URL = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(USERNAME,PASSWORD,HOSTNAME,PORT,DATABASE)
engine = create_engine(DB_URL)

Base = declarative_base() 

class newsdb(object):
    def __init__(self) -> None:
        self.session = None
        self.top_news_class = None

    def openSession(self):
        if self.session is None: 
            self.connectdb()
        return self.session

    def closeSession(self):
        if self.session is None:
            self.session.close()

    def connectdb(self):
        mySession = sessionmaker(bind=engine) 
        self.session = mySession()

    def get_dict_from_obj(self, obj=None):
        if (obj == None):
            return None
        temp = {}
        #attr = [a for a in dir(obj) if not a.startswith('_') and not callable(getattr(obj, a))]
        #print ('********************************************')
        #for a in attr:
        #    print (a, getattr(obj, a), type(getattr(obj, a)))
        attr = [a for a in dir(obj) if not a.startswith('_') and not callable(getattr(obj, a)) and 
                (type(getattr(obj, a)) == type('strings') or
                type(getattr(obj, a)) == datetime.datetime or 
                type(getattr(obj, a)) == datetime.date)]
        for a in attr:
            temp.update({a:getattr(obj, a)})
        return temp

    def get_obj_from_dict(self, cat_dict, obj=None): 
        if (obj == None):
            return None
        for a in cat_dict:
            try:
                setattr(obj, a, cat_dict[a])
            except:
                print ('[%s]:%s'%(a, cat_dict[a]))
        return obj

    def queryTable(self):
        with engine.connect() as conn:
            table_list = []
            result = conn.execute(text("show tables"))
            for index in result:
                table_list.append(index[0])
            return table_list

    def create_top_news_class(self):
        if self.top_news_class == None:
            new_class = type('NewsTop', (Base, ), dict(
                __tablename__ = 'top_news',
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
            self.top_news_class = new_class
        return self.top_news_class

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
        meta.create_all(engine)

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

    def deleteNewsByName(self, ID):
        if self.session is None:
            self.connectdb()
        if ID is None or len(ID.strip()) == 0:
            return None
        CatSurvey = self.create_cat_survey_class()
        result = self.session.query(CatSurvey).filter(CatSurvey.ID == ID).delete(synchronize_session=False) 
        self.session.flush()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result
'''
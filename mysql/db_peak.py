import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DATETIME, DATE, Text, VARCHAR, JSON
from sqlalchemy.orm import sessionmaker, relationship
import pymysql
import datetime
from pathlib import Path
import os
import time

HOSTNAME = os.environ['HOSTNAME']
DATABASE = 'kanos_peak'
PORT = int(os.environ['PORT'])
USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']
DB_URL = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(USERNAME,PASSWORD,HOSTNAME,PORT,DATABASE)
engine = create_engine(DB_URL)

Base = declarative_base() 

class peakdb(object):
    def __init__(self) -> None:
        self.session = None
        self.dog_peak_class = None

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

    def get_dict_from_obj(self, obj):
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

    def get_obj_from_dict(self, tmp_dict, obj): 
        for a in tmp_dict:
            try:
                setattr(obj, a, tmp_dict[a])
            except:
                print ('[%s]:%s'%(a, tmp_dict[a]))
        return obj

    def queryTable(self):
        with engine.connect() as conn:
            table_list = []
            result = conn.execute(text("show tables"))
            for index in result:
                table_list.append(index[0])
            return table_list

################### Dog Peaks Part Start #############################
    def create_dog_peaks_class(self):
        if self.dog_peak_class == None:
            new_class = type('DogPeaks', (Base, ), dict(
                __tablename__ = 'dog_peaks',
                # Primary key
                ID = Column(String(255), primary_key=True),
                Date = Column(DATE, nullable=True),
                Type = Column(Text, nullable=True),
                Input = Column(JSON, nullable=True),
                Output = Column(JSON, nullable=True),
                Reserve = Column(Text, nullable=True),
            ))
            self.dog_peak_class = new_class
        return self.dog_peak_class

    def create_peak_table(self):
        meta = MetaData()
        table_name = Table(
            'dog_peaks', meta,
            # Primary key
            Column('ID', String(255), primary_key=True),
            # Other keys
            Column('Date', DATE, nullable=True),
            Column('Type', Text, nullable=True),
            Column('Input', JSON, nullable=True),
            Column('Output', JSON, nullable=True),
            Column('Reserve', Text, nullable=True),
        )
        meta.create_all(engine)

    def queryDogPeaksAll(self):
        if self.session is None:
            self.connectdb()
        DogPeaks = self.create_dog_peaks_class()
        result = self.session.query(DogPeaks).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryDogPeaksByType(self, region_type):
        if self.session is None:
            self.connectdb()
        DogPeaks = self.create_dog_peaks_class()
        result = self.session.query(DogPeaks).filter(DogPeaks.Type == region_type).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryDogPeaksByID(self, dog_id):
        if self.session is None:
            self.connectdb()
        DogPeaks = self.create_dog_peaks_class()
        result = self.session.query(DogPeaks).filter(DogPeaks.ID == dog_id).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def updateDogPeaksByID(self, dog_id, peak_dict):
        if self.session is None:
            self.connectdb()
        if (len(self.queryDogPeaksByID(dog_id)) > 0):
            DogPeaks = self.create_dog_peaks_class()
            self.session.query(DogPeaks).filter(DogPeaks.ID == dog_id).update(peak_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            return self.insertDogPeaks(dog_id, peak_dict)

    def insertDogPeaks(self, dog_id, peak_dict):
        if self.session is None:
            self.connectdb()
        DogPeaks = self.create_dog_peaks_class()
        dog = DogPeaks()
        dog = self.get_obj_from_dict(peak_dict, dog)
        try:
            self.session.add(dog)
            self.session.commit()
        except:
            return False
        else:
            return True

################### Dog Money Part End ###############################

if __name__ == '__main__':
    pass

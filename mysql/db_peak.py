#!/bin/python3

# System lib
import os, sys
import time, datetime
from sqlalchemy import MetaData, Table
from sqlalchemy import Column, Integer, String, DATETIME, DATE, Text, VARCHAR, JSON

# Customsized lib
import db_base as dbb

class peakdb(dbb.basedb):
    def create_dog_peaks_class(self):
        table_name = 'dog_peaks'
        if table_name not in self.db_class:
            new_class = type('DogPeaks', (self.Base, ), dict(
                __tablename__ = table_name,
                # Primary key
                ID = Column(String(255), primary_key=True),
                Date = Column(DATE, nullable=True),
                Type = Column(Text, nullable=True),
                Input = Column(JSON, nullable=True),
                Output = Column(JSON, nullable=True),
                Reserve = Column(Text, nullable=True),
            ))
            self.db_class.update({table_name:new_class})
        return self.db_class[table_name]

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
        meta.create_all(self.engine)

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

if __name__ == '__main__':
    pass

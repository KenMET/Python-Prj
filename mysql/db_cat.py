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
DATABASE = 'kanos_cat'
PORT = int(os.environ['PORT'])
USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']
DB_URL = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(USERNAME,PASSWORD,HOSTNAME,PORT,DATABASE)
engine = create_engine(DB_URL)

Base = declarative_base() 
'''
class CatSurvey(Base):
    __tablename__ = 'cat_survey'
    # Primary key
    ID = Column(VARCHAR, primary_key=True) 
    # Other keys
    Name = Column(Text, nullable=True)
    Type = Column(Text, nullable=True)
    AssetSize = Column(Text, nullable=True)
    Custodian = Column(Text, nullable=True)
    DividendPolicy = Column(Text, nullable=True)
    EstablishmentDate_Size = Column(Text, nullable=True)
    EstablishmentDividend = Column(Text, nullable=True)
    HostingFees = Column(Text, nullable=True)
    InvestmentObjectives = Column(Text, nullable=True)
    InvestmentPhilosophy = Column(Text, nullable=True)
    InvestmentScope = Column(Text, nullable=True)
    InvestmentStrategy = Column(Text, nullable=True)
    ManagementFeeRate = Column(Text, nullable=True)
    Manager = Column(Text, nullable=True)
    ManagerPerson = Column(Text, nullable=True)
    MaximumApplyRate = Column(Text, nullable=True)
    MaximumRedemptionRate = Column(Text, nullable=True)
    MaximumSubscriptionRate = Column(Text, nullable=True)
    PerformanceComparisonBase = Column(Text, nullable=True)
    PublishDate = Column(Text, nullable=True)
    RiskReturnCharacteristics = Column(Text, nullable=True)
    SalesServiceRate = Column(Text, nullable=True)
    ShareSize = Column(Text, nullable=True)
    TargetTrack = Column(Text, nullable=True)
    Reserve = Column(Text, nullable=True)
'''
class catdb(object):
    def __init__(self) -> None:
        self.session = None
        self.cat_survey_class = None
        self.cat_net_class = {}
        self.cat_net_rt_class = {}
        self.cat_holding_class = {}

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

    def create_cat_survey_class(self):
        if self.cat_survey_class == None:
            new_class = type('CatSurvey', (Base, ), dict(
                __tablename__ = 'cat_survey',
                ID = Column(String(255), primary_key=True),
                Name = Column(Text, nullable=True),
                Type = Column(Text, nullable=True),
                AssetSize = Column(Text, nullable=True),
                Custodian = Column(Text, nullable=True),
                DividendPolicy = Column(Text, nullable=True),
                EstablishmentDate_Size = Column(Text, nullable=True),
                EstablishmentDividend = Column(Text, nullable=True),
                HostingFees = Column(Text, nullable=True),
                InvestmentObjectives = Column(Text, nullable=True),
                InvestmentPhilosophy = Column(Text, nullable=True),
                InvestmentScope = Column(Text, nullable=True),
                InvestmentStrategy = Column(Text, nullable=True),
                ManagementFeeRate = Column(Text, nullable=True),
                Manager = Column(Text, nullable=True),
                ManagerPerson = Column(Text, nullable=True),
                MaximumApplyRate = Column(Text, nullable=True),
                MaximumRedemptionRate = Column(Text, nullable=True),
                MaximumSubscriptionRate = Column(Text, nullable=True),
                PerformanceComparisonBase = Column(Text, nullable=True),
                PublishDate = Column(Text, nullable=True),
                RiskReturnCharacteristics = Column(Text, nullable=True),
                SalesServiceRate = Column(Text, nullable=True),
                ShareSize = Column(Text, nullable=True),
                TargetTrack = Column(Text, nullable=True),
                Reserve = Column(Text, nullable=True),
            ))
            self.cat_survey_class = new_class
        return self.cat_survey_class

    def create_cat_net_class(self, cat_id):
        if cat_id not in self.cat_net_class:
            new_class = type('CatNet%s'%(cat_id), (Base, ), dict(
                __tablename__ = 'cat_net_%s'%(cat_id),
                NetValueDate = Column(DATE, primary_key=True),
                NetValueUnit = Column(Text, nullable=True),
                NetValueCumulative = Column(Text, nullable=True),
                DayGrowth = Column(Text, nullable=True),
                SubscriptionStatus = Column(Text, nullable=True),
                RedemptionStatus = Column(Text, nullable=True),
                DividendsSending = Column(Text, nullable=True),
                Reserve = Column(Text, nullable=True)
            ))
            self.cat_net_class.update({cat_id:new_class})
        return self.cat_net_class[cat_id]

    def create_cat_net_rt_class(self, cat_id):
        if cat_id not in self.cat_net_rt_class:
            new_class = type('CatNetRT%s'%(cat_id), (Base, ), dict(
                __tablename__ = 'cat_net_rt_%s'%(cat_id),
                NetValueTime = Column(DATETIME, primary_key=True),
                NetValueCurrent = Column(Text, nullable=True),
                NetValueCurrentGrowth = Column(Text, nullable=True),
                NetValueUnit = Column(Text, nullable=True),
                Reserve = Column(Text, nullable=True)
            ))
            self.cat_net_rt_class.update({cat_id:new_class})
        return self.cat_net_rt_class[cat_id]

    def create_cat_holding_class(self, cat_id):
        if cat_id not in self.cat_holding_class:
            new_class = type('CatHolding%s'%(cat_id), (Base, ), dict(
                __tablename__ = 'cat_holding_%s'%(cat_id),
                DogCodeQuarter = Column(String(255), primary_key=True),
                DogName = Column(Text, nullable=True),
                DogProportion = Column(Text, nullable=True),
                DogShare = Column(Text, nullable=True),
                DogMarketValue = Column(Text, nullable=True),
                Reserve = Column(Text, nullable=True)
            ))
            self.cat_holding_class.update({cat_id:new_class})
        return self.cat_holding_class[cat_id]

    def queryCatNetRTAll(self, cat_id):
        if self.session is None:
            self.connectdb()
        CatNetRT = self.create_cat_net_rt_class(cat_id)
        result = self.session.query(CatNetRT).all() 
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryCatNetAll(self, cat_id):
        if self.session is None:
            self.connectdb()
        CatNet = self.create_cat_net_class(cat_id)
        result = self.session.query(CatNet).all() 
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryCatRTAll(self, cat_id):
        if self.session is None:
            self.connectdb()
        CatNet = self.create_cat_net_rt_class(cat_id)
        result = self.session.query(CatNet).all() 
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryLastCatRT(self, cat_id):
        if self.session is None:
            self.connectdb()
        CatNet = self.create_cat_net_rt_class(cat_id)
        result = self.session.query(CatNet).order_by(sqlalchemy.desc(CatNet.NetValueTime)).first()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryCatAll(self):
        if self.session is None:
            self.connectdb()
        CatSurvey = self.create_cat_survey_class()
        result = self.session.query(CatSurvey).all() 
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryCatByID(self, ID):
        if self.session is None:
            self.connectdb()
        CatSurvey = self.create_cat_survey_class()
        result = self.session.query(CatSurvey).filter(CatSurvey.ID == ID).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result
    
    def queryLastCatNet(self, cat_id):
        if self.session is None:
            self.connectdb()
        CatNet = self.create_cat_net_class(cat_id)
        result = self.session.query(CatNet).order_by(sqlalchemy.desc(CatNet.NetValueDate)).first()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryCatNetByTime(self, cat_id, Time):
        if self.session is None:
            self.connectdb()
        CatNet = self.create_cat_net_rt_class(cat_id)
        result = self.session.query(CatNet).filter(CatNet.NetValueTime == Time).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryCatNetByDate(self, cat_id, Date):
        if self.session is None:
            self.connectdb()
        CatNet = self.create_cat_net_class(cat_id)
        result = self.session.query(CatNet).filter(CatNet.NetValueDate == Date).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryLastCatHolding(self, cat_id):
        if self.session is None:
            self.connectdb()
        CatHolding = self.create_cat_holding_class(cat_id)
        result = self.session.query(CatHolding).order_by(sqlalchemy.desc(CatHolding.DogCodeQuarter)).first()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryCatHoldingByQuarter(self, cat_id, quarter):
        if self.session is None:
            self.connectdb()
        CatHolding = self.create_cat_holding_class(cat_id)
        result = self.session.query(CatHolding).filter(CatHolding.DogCodeQuarter.like('%{0}%'.format(quarter))).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def queryCatHoldingByCodeQuarter(self, cat_id, code_quarter):
        if self.session is None:
            self.connectdb()
        CatHolding = self.create_cat_holding_class(cat_id)
        result = self.session.query(CatHolding).filter(CatHolding.DogCodeQuarter == code_quarter).all()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def countCatByID(self, ID):
        ret = self.queryCatByID(ID)
        count = 0
        for index in ret:
            count += 1
        return count
    
    def countCatNetByDate(self, cat_id, date):
        ret = self.queryCatNetByDate(cat_id, date)
        count = 0
        for index in ret:
            count += 1
        return count

    def countCatNetByCodeQuarter(self, cat_id, code_quarter):
        ret = self.queryCatHoldingByCodeQuarter(cat_id, code_quarter)
        count = 0
        for index in ret:
            count += 1
        return count

    def countCatNetByTime(self, cat_id, time):
        ret = self.queryCatNetByTime(cat_id, time)
        count = 0
        for index in ret:
            count += 1
        return count

    def updateCatSurveyByID(self, ID, cat_dict):
        if self.session is None:
            self.connectdb()
        if (self.countCatByID(ID) > 0):
            CatSurvey = self.create_cat_survey_class()
            self.session.query(CatSurvey).filter(CatSurvey.ID == ID).update(cat_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            cat_dict.update({'ID':ID})
            return self.insertCatSurvey(cat_dict)

    def updateCatNetByTime(self, cat_id, time, cat_dict):
        if self.session is None:
            self.connectdb()
        if (self.countCatNetByTime(cat_id, time) > 0):
            CatNet = self.create_cat_net_rt_class(cat_id)
            self.session.query(CatNet).filter(CatNet.NetValueTime == time).update(cat_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            cat_dict.update({'NetValueTime':time})
            return self.insertCatNet(cat_id, cat_dict)

    def updateCatNetByDate(self, cat_id, date, cat_dict):
        if self.session is None:
            self.connectdb()
        if (self.countCatNetByDate(cat_id, date) > 0):
            CatNet = self.create_cat_net_class(cat_id)
            self.session.query(CatNet).filter(CatNet.NetValueDate == date).update(cat_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            cat_dict.update({'NetValueDate':date})
            return self.insertCatNet(cat_id, cat_dict)

    def updateCatHoldingByCodeQuarter(self, cat_id, code_quarter, cat_dict):
        if self.session is None:
            self.connectdb()
        if (self.countCatNetByCodeQuarter(cat_id, code_quarter) > 0):
            CatHolding = self.create_cat_holding_class(cat_id)
            self.session.query(CatHolding).filter(CatHolding.DogCodeQuarter == code_quarter).update(cat_dict)
            try:
                self.session.commit()
            except:
                return False
            else:
                return True
        else:
            return self.insertCatHolding(cat_id, cat_dict)

    def insertCatSurvey(self, cat_dict):
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

    def insertCatHolding(self, cat_id, cat_dict):
        if self.session is None:
            self.connectdb()
        if (self.countCatNetByCodeQuarter(cat_id, cat_dict['DogCodeQuarter']) > 0):
            return False
        CatHolding = self.create_cat_holding_class(cat_id)
        cat = CatHolding()
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

    def insertCatNet(self, cat_id, cat_dict):
        if self.session is None:
            self.connectdb()
        if (self.countCatNetByDate(cat_id, cat_dict['NetValueDate']) > 0):
            return False
        CatNet = self.create_cat_net_class(cat_id)
        cat = CatNet()
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

    def insertCatNetRT(self, cat_id, cat_dict):
        if self.session is None:
            self.connectdb()
        if (self.countCatNetByTime(cat_id, cat_dict['NetValueTime']) > 0):
            return False
        CatNet = self.create_cat_net_rt_class(cat_id)
        cat = CatNet()
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

    def deleteCatByID(self, ID):
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

    def deleteCatRTByID(self, cat_id):
        if self.session is None:
            self.connectdb()
        if cat_id is None or len(cat_id.strip()) == 0:
            return None
        CatNet = self.create_cat_net_rt_class(cat_id)
        result = self.session.query(CatNet).delete(synchronize_session=False) 
        self.session.flush()
        try:
            self.session.commit()
        except:
            return []
        else:
            return result

    def create_survey_table(self):
        meta = MetaData()
        table_name = Table(
            'cat_survey', meta,
            # Primary key
            Column('ID', String(255), primary_key=True),
            # Other keys
            Column('Name', Text, nullable=True),
            Column('Type', Text, nullable=True),
            Column('AssetSize', Text, nullable=True),
            Column('Custodian', Text, nullable=True),
            Column('DividendPolicy', Text, nullable=True),
            Column('EstablishmentDate_Size', Text, nullable=True),
            Column('EstablishmentDividend', Text, nullable=True),
            Column('HostingFees', Text, nullable=True),
            Column('InvestmentObjectives', Text, nullable=True),
            Column('InvestmentPhilosophy', Text, nullable=True),
            Column('InvestmentScope', Text, nullable=True),
            Column('InvestmentStrategy', Text, nullable=True),
            Column('ManagementFeeRate', Text, nullable=True),
            Column('Manager', Text, nullable=True),
            Column('ManagerPerson', Text, nullable=True),
            Column('MaximumApplyRate', Text, nullable=True),
            Column('MaximumRedemptionRate', Text, nullable=True),
            Column('MaximumSubscriptionRate', Text, nullable=True),
            Column('PerformanceComparisonBase', Text, nullable=True),
            Column('PublishDate', Text, nullable=True),
            Column('RiskReturnCharacteristics', Text, nullable=True),
            Column('SalesServiceRate', Text, nullable=True),
            Column('ShareSize', Text, nullable=True),
            Column('TargetTrack', Text, nullable=True),
            Column('Reserve', Text, nullable=True),
        )
        meta.create_all(engine)

    def create_net_rt_table(self, table_name):
        meta = MetaData()
        table_name = Table(
            table_name, meta,
            # Primary key
            Column('NetValueTime', DATE, primary_key=True),
            # Other keys
            Column('NetValueCurrent', Text, nullable=True),
            Column('NetValueCurrentGrowth', Text, nullable=True),
            Column('NetValueUnit', Text, nullable=True),
            Column('Reserve', Text, nullable=True),
        )
        meta.create_all(engine)

    def create_net_table(self, table_name):
        meta = MetaData()
        table_name = Table(
            table_name, meta,
            # Primary key
            Column('NetValueDate', DATE, primary_key=True),
            # Other keys
            Column('NetValueUnit', Text, nullable=True),
            Column('NetValueCumulative', Text, nullable=True),
            Column('DayGrowth', Text, nullable=True),
            Column('SubscriptionStatus', Text, nullable=True),
            Column('RedemptionStatus', Text, nullable=True),
            Column('DividendsSending', Text, nullable=True),
            Column('Reserve', Text, nullable=True),
        )
        meta.create_all(engine)

    def create_holding_table(self, table_name):
        meta = MetaData()
        table_name = Table(
            table_name, meta,
            # Primary key
            Column('DogCodeQuarter', String(255), primary_key=True),
            # Other keys
            Column('DogName', Text, nullable=True),
            Column('DogProportion', Text, nullable=True),
            Column('DogShare', Text, nullable=True),
            Column('DogMarketValue', Text, nullable=True),
            Column('Reserve', Text, nullable=True),
        )
        meta.create_all(engine)

    def queryTable(self):
        with engine.connect() as conn:
            table_list = []
            result = conn.execute(text("show tables"))
            for index in result:
                table_list.append(index[0])
            return table_list


if __name__ == '__main__':
    db = catdb()
    db.openSession()

    print (db.countCatByID('001593_Insert_Test'))

    db.deleteCatByID('001593_Insert_Test')
    ret_temp = db.queryCatByID('001593_Insert_Test')
    for index in ret_temp:
        temp_dict = db.get_dict_from_obj(index)
        for member in temp_dict:
            print ('[%s]:%s'%(member, temp_dict[member]))
            pass

    exit()
    '''
    ret = db.queryCatAll()
    for index in ret:
        temp_dict = db.get_dict_from_obj(index)
        for member in temp_dict:
            #print ('[%s]:%s'%(member, temp_dict[member]))
            pass
        obj_temp = db.get_obj_from_dict(temp_dict)
        temp_dict_obj = db.get_dict_from_obj(obj_temp)
        for member in temp_dict_obj:
            #print ('[%s]:%s'%(member, temp_dict_obj[member]))
            pass
    '''

    ret = db.queryCatByID('001593')
    for index in ret:
        temp_dict = db.get_dict_from_obj(index)
        for member in temp_dict:
            #print ('[%s]:%s'%(member, temp_dict[member]))
            pass
        
        '''
        temp_dict.update({'Type':'Modify Test2'})
        db.updateCatSurveyByID(temp_dict['ID'], temp_dict)
        ret_temp = db.queryCatByID('001593')
        for index in ret_temp:
            temp_dict = db.get_dict_from_obj(index)
            for member in temp_dict:
                #print ('[%s]:%s'%(member, temp_dict[member]))
                pass
        '''
        temp_dict.update({'ID':'001593_Insert_Test'})
        flag = db.insertCatSurvey(temp_dict)
        print (flag)
        ret_temp = db.queryCatByID('001593_Insert_Test')
        for index in ret_temp:
            temp_dict = db.get_dict_from_obj(index)
            for member in temp_dict:
                print ('[%s]:%s'%(member, temp_dict[member]))
                pass

    exit()

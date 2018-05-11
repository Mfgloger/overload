from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, ForeignKey, Integer, String,
                        create_engine)
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from contextlib import contextmanager


from setup_dirs import DATASTORE

Base = declarative_base()
conn_string = 'sqlite:///{}'.format(DATASTORE)


class PVR_Batch(Base):
    """PVR module batch information"""
    __tablename__ = 'pvr_batch'
    bid = Column(Integer, primary_key=True)
    timestamp = Column(String, default=datetime.now())
    system = Column(String, nullable=False)
    library = Column(String, nullable=False)
    agent = Column(String, nullable=False)
    file_qty = Column(Integer, default=0)

    files = relationship('PVR_File', cascade='all, delete-orphan')

    def __repr__(self):
        return "<PVR_Batch(bid='%s', timestamp='%s', " \
            "system='%s', library='%s', " \
            "agent='%s, file_qty='%s')>" % (
                self.bid,
                self.timestamp,
                self.system,
                self.library,
                self.agent,
                self.file_qty)


class PVR_File(Base):
    """PVR module file stats"""
    __tablename__ = 'pvr_file'
    fid = Column(Integer, primary_key=True)
    bid = Column(Integer, ForeignKey('pvr_batch.bid'), nullable=False)
    vid = Column(Integer, ForeignKey('vendor.vid'), nullable=False)
    new = Column(Integer, default=0)
    dups = Column(Integer, default=0)
    updated = Column(Integer, default=0)
    mixed = Column(Integer, default=0)
    other = Column(Integer, default=0)

    def __repr__(self):
        return "<PVR_File(file_id='%s', batch_id='%s', vendor_id='%s', " \
            "new='%s', dups='%s', updated='%s', mixed='%s', " \
            "other='%s')>" % (
                self.fid, self.bid, self.vid,
                self.new,
                self.dups,
                self.updated,
                self.mixed,
                self.other)


class Vendor(Base):
    """PVR module vendor data"""
    __tablename__ = 'vendor'
    vid = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, default='UNKNOWN')

    def __repr__(self):
        return "<Vendor(vendor_id='%s', name='%s)>" % (
            self.vid,
            self.name)


class NYPLOrderTemplate(Base):
    """NYPL order templates data"""

    __tablename__ = 'NyplOrderTemplate'
    otid = Column(Integer, primary_key=True)
    tName = Column(String, nullable=False, unique=True)
    acqType = Column(String)
    claim = Column(String)
    code1 = Column(String)
    code2 = Column(String)
    code3 = Column(String)
    code4 = Column(String)
    form = Column(String)
    orderNote = Column(String)
    orderType = Column(String)
    status = Column(String, nullable=False, default='1')
    vendor = Column(String)
    lang = Column(String)
    country = Column(String)
    identity = Column(String)
    generalNote = Column(String)
    internalNote = Column(String)
    oldOrdNo = Column(String)
    selector = Column(String)
    venAddr = Column(String)
    venNote = Column(String)
    blanketPO = Column(String)
    venTitleNo = Column(String)
    paidNote = Column(String)
    shipTo = Column(String)
    requestor = Column(String)
    bibFormat = Column(String)  # sets Sierra record format; is this needed?
    match1st = Column(String, nullable=False)
    match2nd = Column(String)
    match3rd = Column(String)

    def __repr__(self):
        return "<NyplOrderTemplate(otid='%s', tName='%s', acqType='%s', " \
            "claim='%s', code1='%s', code2='%s', code3='%s', code4='%s', " \
            "form='%s', orderType='%s', orderNote='%s', status='%s', " \
            "vendor='%s', lang='%s', country='%s', identity='%s', " \
            "generalNote='%s', internalNote='%s', oldOrdNo='%s', " \
            "selector='%s', venAddr='%s', venNote='%s', venTitleNo='%s', " \
            "blanketPO='%s', paidNote='%s', shipTo='%s', requestor='%s', " \
            "bibFormat='%s, match1st='%s', match2nd='%s', match3rd='%s')>" % (
                self.otid, self.tName, self.acqType, self.claim,
                self.code1, self.code2, self.code3, self.code4,
                self.form, self.orderType, self.orderNote, self.status,
                self.vendor, self.lang, self.country,
                self.identity, self.generalNote, self.internalNote,
                self.oldOrdNo, self.selector, self.venAddr, self.venNote,
                self.venTitleNo, self.blanketPO, self.paidNote, self.shipTo,
                self.requestor, self.bibFormat, self.match1st, self.match2nd,
                self.match3rd
            )


class FTPs(Base):
    """Stores vendor FTP details"""
    __tablename__ = 'ftps'
    fid = Column(Integer, primary_key=True)
    host = Column(String, nullable=False, unique=True)
    user = Column(String)
    password = Column(String)
    system = Column(String, nullable=False)

    def __repr__(self):
        return "<FTPs(fid='%s', host='%s', user='%s', password='%s', " \
            "system='%s')>" % (
                self.fid, self.host, self.user, self.password, self.system)


class DataAccessLayer:

    def __init__(self):
        self.conn_string = conn_string
        self.engine = None
        self.session = None

    def connect(self):
        self.engine = create_engine(self.conn_string)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)


dal = DataAccessLayer()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    dal.connect()
    session = dal.Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

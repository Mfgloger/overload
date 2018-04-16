from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, ForeignKey, Integer, String, Boolean,
                        create_engine)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.exc import IntegrityError
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

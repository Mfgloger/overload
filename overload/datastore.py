from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    PickleType,
    String,
    create_engine,
)
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from contextlib import contextmanager


from setup_dirs import DATASTORE

Base = declarative_base()
conn_string = "sqlite:///{}".format(DATASTORE)


class PVR_Batch(Base):
    """PVR module batch information"""

    __tablename__ = "pvr_batch"
    bid = Column(Integer, primary_key=True)
    timestamp = Column(String, default=datetime.now())
    system = Column(String, nullable=False)
    library = Column(String, nullable=False)
    agent = Column(String, nullable=False)
    file_qty = Column(Integer, default=0)

    files = relationship("PVR_File", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            "<PVR_Batch(bid='%s', timestamp='%s', "
            "system='%s', library='%s', "
            "agent='%s, file_qty='%s')>"
            % (
                self.bid,
                self.timestamp,
                self.system,
                self.library,
                self.agent,
                self.file_qty,
            )
        )


class PVR_File(Base):
    """PVR module file stats"""

    __tablename__ = "pvr_file"
    fid = Column(Integer, primary_key=True)
    bid = Column(Integer, ForeignKey("pvr_batch.bid"), nullable=False)
    vid = Column(Integer, ForeignKey("vendor.vid"), nullable=False)
    new = Column(Integer, default=0)
    dups = Column(Integer, default=0)
    updated = Column(Integer, default=0)
    mixed = Column(Integer, default=0)
    other = Column(Integer, default=0)

    def __repr__(self):
        return (
            "<PVR_File(file_id='%s', batch_id='%s', vendor_id='%s', "
            "new='%s', dups='%s', updated='%s', mixed='%s', "
            "other='%s')>"
            % (
                self.fid,
                self.bid,
                self.vid,
                self.new,
                self.dups,
                self.updated,
                self.mixed,
                self.other,
            )
        )


class Vendor(Base):
    """PVR module vendor data"""

    __tablename__ = "vendor"
    vid = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, default="UNKNOWN")

    def __repr__(self):
        return "<Vendor(vendor_id='%s', name='%s)>" % (self.vid, self.name)


class NYPLOrderTemplate(Base):
    """NYPL order templates data"""

    __tablename__ = "NyplOrderTemplate"
    otid = Column(Integer, primary_key=True)
    tName = Column(String, nullable=False, unique=True)
    agent = Column(String, nullable=False)
    acqType = Column(String)
    claim = Column(String)
    code1 = Column(String)
    code2 = Column(String)
    code3 = Column(String)
    code4 = Column(String)
    raction = Column(String)
    form = Column(String)
    orderNote = Column(String)
    orderType = Column(String)
    status = Column(String, nullable=False, default="1")
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
        return (
            "<NyplOrderTemplate(otid='%s', tName='%s', acqType='%s', "
            "claim='%s', code1='%s', code2='%s', code3='%s', code4='%s', "
            "raction='%s', form='%s', orderType='%s', orderNote='%s', "
            "status='%s', vendor='%s', lang='%s', country='%s', "
            "identity='%s', generalNote='%s', internalNote='%s', "
            "oldOrdNo='%s', selector='%s', venAddr='%s', venNote='%s', "
            "venTitleNo='%s', blanketPO='%s', paidNote='%s', shipTo='%s', "
            "requestor='%s', bibFormat='%s, match1st='%s', match2nd='%s', "
            "match3rd='%s')>"
            % (
                self.otid,
                self.tName,
                self.acqType,
                self.claim,
                self.code1,
                self.code2,
                self.code3,
                self.code4,
                self.raction,
                self.form,
                self.orderType,
                self.orderNote,
                self.status,
                self.vendor,
                self.lang,
                self.country,
                self.identity,
                self.generalNote,
                self.internalNote,
                self.oldOrdNo,
                self.selector,
                self.venAddr,
                self.venNote,
                self.venTitleNo,
                self.blanketPO,
                self.paidNote,
                self.shipTo,
                self.requestor,
                self.bibFormat,
                self.match1st,
                self.match2nd,
                self.match3rd,
            )
        )


class FTPs(Base):
    """Stores vendor FTP details"""

    __tablename__ = "ftps"
    fid = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    host = Column(String, nullable=False)
    folder = Column(String)
    user = Column(String)
    password = Column(String)
    system = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint("name", "system"),)

    def __repr__(self):
        return (
            "<FTPs(fid='%s', name='%s', host='%s', folder='%s', "
            "user='%s', password='%s', system='%s')>"
            % (
                self.fid,
                self.name,
                self.host,
                self.folder,
                self.user,
                self.password,
                self.system,
            )
        )


class WCSourceBatch(Base):
    """Worldcat module source file data"""

    __tablename__ = "wc_source_batch"
    wcsbid = Column(Integer, primary_key=True)
    file = Column(String, nullable=False)
    system = Column(String, nullable=False)
    library = Column(String)
    action = Column(String, nullable=False)
    api = Column(String, nullable=False)
    data_source = Column(String, nullable=False)
    encode_level = Column(String, nullable=False)
    mat_type = Column(String, nullable=False)
    cat_rules = Column(String, nullable=False)
    cat_source = Column(String, nullable=False)
    id_type = Column(String)

    meta = relationship("WCSourceMeta", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            "<WCSourceBatch(wcsid=%s, file=%s, system='%s', "
            "library='%s', action='%s', api='%s', data_source='%s', "
            "encode_level='%s', mat_type='%s', cat_rules='%s', "
            "cat_source='%s', id_type='%s')>"
            % (
                self.wcsbid,
                self.file,
                self.system,
                self.library,
                self.action,
                self.api,
                self.data_source,
                self.encode_level,
                self.mat_type,
                self.cat_rules,
                self.cat_source,
                self.id_type,
            )
        )


class WCSourceMeta(Base):
    """Worldcat module individual bib/order metadata"""

    __tablename__ = "wc_source_meta"
    wcsmid = Column(Integer, primary_key=True)
    wcsbid = Column(Integer, ForeignKey("wc_source_batch.wcsbid"), nullable=False)
    selected = Column(Boolean, default=False)
    barcode = Column(String)
    meta = Column(PickleType)

    wchits = relationship(
        "WCHit", cascade="all, delete-orphan", uselist=False, lazy="joined"
    )

    def __repr__(self):
        return (
            "<WCSourceMeta(wcsmid=%s, wcsbid=%s, selected='%s', "
            "barcode='%s')>" % (self.wcsmid, self.wcsbid, self.selected, self.barcode)
        )


class WCHit(Base):
    """
    Worldcat results
    """

    __tablename__ = "wc_hit"
    wchid = Column(Integer, primary_key=True)
    wcsmid = Column(Integer, ForeignKey("wc_source_meta.wcsmid"), nullable=False)
    hit = Column(Boolean, nullable=False)
    query_results = Column(PickleType)
    match_oclcNo = Column(String, default=None)
    match_marcxml = Column(PickleType)
    prepped_marc = Column(PickleType)
    holding_set = Column(Boolean, default=False)
    holdings_status = Column(String)
    holding_response = Column(PickleType)

    def __repr__(self):
        return (
            "<WCHit(wchid=%s, wcsmid=%s, hit=%s, match_oclcNo=%s,"
            "holding_set=%s)>"
            % (self.wchid, self.wcsmid, self.hit, self.match_oclcNo, self.holding_set)
        )


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

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    SmallInteger,
    BigInteger,
    String,
    Date,
    ForeignKey,
    UniqueConstraint
    )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship
    )
from ..tools import as_timezone
from ..models import Base, CommonModel, DefaultModel, DBSession
    
class Propinsi(Base, DefaultModel):
    __tablename__ = 'propinsis'
    __table_args__ = {'extend_existing':True}
    kode = Column(String(2), unique=True, nullable=False)
    nama = Column(String(30), unique=True, nullable=False)
    
    @classmethod
    def get_deferred(cls):
        return DBSession.query(cls.id, cls.nama).order_by(cls.kode).all()

class Dati2(Base, DefaultModel):
    __tablename__ = 'dati2s'
    __table_args__ = (UniqueConstraint('propinsi_id','kode', name="dati2_kode_key"),
                      {'extend_existing':True})
    kode = Column(String(2), nullable=False)
    nama = Column(String(30), unique=True, nullable=False)
    propinsi_id = Column(Integer, ForeignKey('propinsis.id')) 
    propinsi = relationship("Propinsi", backref="dati2")
    
    @classmethod
    def get_by_kode(cls, propinsi_id, kode):
        return cls.query().filter_by(propinsi_id=propinsi_id,kode=kode).first()      
    
    @classmethod
    def get_deferred(cls):
        return DBSession.query(cls.id, cls.nama).order_by(cls.kode).all()    
        
class Registers(Base, DefaultModel):
    __tablename__ = 'registers'
    __table_args__ = {'extend_existing':True}
    kode = Column(String(5), unique=True, nullable=False)
    nama = Column(String(30), unique=True, nullable=False)
    alamat_pemda = Column(String(128), unique=True, nullable=False)
    nama_pic = Column(String(30), nullable=False)
    nip_pic  = Column(String(18), unique=True, nullable=False)
    no_telpon = Column(String(18), unique=True, nullable=False)
    no_hp = Column(String(18), unique=True, nullable=False)
    tgl_register = Column(Date, nullable=False)
    tgl_update = Column(Date, nullable=True)
    tgl_valid = Column(Date, nullable=False)
    status = Column(SmallInteger, nullable=False, default=0)
    e_mail = Column(String(32), unique=True, nullable=False)
    jns_bayar = Column(SmallInteger, nullable=False) #Transfer/Kartu Kredit
    tagih_nama   = Column(String(30), nullable=False)
    tagih_alamat = Column(String(128), nullable=False)
    password     = Column(String(128), nullable=False)
    periode_bayar = Column(SmallInteger, nullable=False)
    rpc_url = Column(String(128), nullable=False)
    rpc_userid = Column(String(128),  nullable=False)
    rpc_password = Column(String(128), unique=True, nullable=False)
    propinsi_id = Column(Integer, ForeignKey('propinsis.id')) 
    propinsi = relationship("Propinsi", backref="register")
    dati2_id = Column(Integer, ForeignKey('dati2s.id')) 
    dati2 = relationship("Dati2", backref="register")
    

class Invoices(Base, DefaultModel):
    __tablename__ = 'invoices'
    __table_args__ = {'extend_existing':True}
    kode = Column(String(5), unique=True, nullable=False)
    nama = Column(String(30), unique=True, nullable=False)
    alamat = Column(String(128), unique=True, nullable=False)
    register_id = Column(Integer, ForeignKey("registers.id"), nullable=False)
    jumlah = Column(BigInteger, nullable = False)
    tgl_invoice  = Column(Date, nullable = False)

    
class Payments(Base, DefaultModel):
    __tablename__ = 'payments'
    __table_args__ = {'extend_existing':True}
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    jumlah     = Column(BigInteger, nullable = False)
    tgl_bayar  = Column(Date, nullable = False)
    jns_bayar  = Column(SmallInteger, nullable = False)
    posted = Column(SmallInteger, nullable=False, default=0)
    

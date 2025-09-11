from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False, unique=True)
    saldo_pendiente = Column(Float, nullable=False, default=0.0)

engine = create_engine('sqlite:///database.db', echo=True)
Session = sessionmaker(bind=engine)

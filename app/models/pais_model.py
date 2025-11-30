from sqlalchemy import Column, String, Float
from app.database import Base

class PaisModel(Base):
    __tablename__ = "paises"
    __table_args__ = {"schema": "defaultdb"}

    id = Column(String(5), primary_key=True)
    nombre = Column(String(100))
    lat = Column(Float)
    lon = Column(Float)

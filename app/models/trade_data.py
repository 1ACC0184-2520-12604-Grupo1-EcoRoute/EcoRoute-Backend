from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TradeData(Base):
    __tablename__ = "trade_data"
    __table_args__ = {"schema": "trade"}   # 👈👈 MUY IMPORTANTE

    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String(100))
    destination = Column(String(100))
    product = Column(String(150))
    quantity = Column(Float)
    unit_price = Column(Float)
    tariff = Column(Float)
    date = Column(String(50))
    total_price = Column(Float)

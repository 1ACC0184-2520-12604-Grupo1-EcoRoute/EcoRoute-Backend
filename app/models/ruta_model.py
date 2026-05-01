from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class RutaModel(Base):
    __tablename__ = "rutas"
    __table_args__ = {"schema": "defaultdb"}

    id = Column(Integer, primary_key=True)
    origen_id = Column(String(5))
    destino_id = Column(String(5))
    tipo = Column(String(20))
    distancia_km = Column(Float)
    tiempo_horas = Column(Float)
    costo_base_usd_ton = Column(Float)

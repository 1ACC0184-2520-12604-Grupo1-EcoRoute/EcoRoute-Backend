# models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

# ==== Usuario (igual a lo que ya tenías) ====
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

# ==== Reporte de rutas calculadas ====
class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    origin = Column(String(150), nullable=False)
    destination = Column(String(150), nullable=False)
    product = Column(String(150), nullable=True)

    # costo total acumulado de la ruta
    cost = Column(Float, nullable=False, default=0.0)

    # camino serializado (JSON como string)
    path = Column(Text, nullable=False, default="[]")

    # algoritmo usado: 'dijkstra' | 'floyd' | 'auto'
    algorithm = Column(String(30), nullable=True)

    def __repr__(self) -> str:
        return f"<Report id={self.id} {self.origin}->{self.destination} {self.product} cost={self.cost}>"

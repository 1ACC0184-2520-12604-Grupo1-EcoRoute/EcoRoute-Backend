# models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    origin = Column(String(120), nullable=False)
    destination = Column(String(120), nullable=False)
    product = Column(String(120), nullable=False)

    cost = Column(Float, nullable=False)
    path = Column(Text, nullable=False)          # JSON string con la ruta
    algorithm = Column(String(50), default="dijkstra")

    user = relationship("User", back_populates="reports")

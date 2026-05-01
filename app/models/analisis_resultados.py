from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class AnalisisResultado(Base):
    __tablename__ = "analisis_resultados"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(255), nullable=False)
    algorithm = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    result_summary = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
    hidden = Column(Boolean, nullable=False, default=False)

    user = relationship("User", backref="analisis_resultados")

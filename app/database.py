# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Lee la URL desde una variable de entorno
# EJEMPLO de valor (solo en tu .env, NO en GitHub):
# DATABASE_URL=mysql+pymysql://avnadmin:TU_PASSWORD@ecoroute-mysql-ecoroute.l.aivencloud.com:16811/defaultdb?ssl_ca=./certs/ca.pem
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está definida. Configúrala en tu .env o en las variables de entorno del servidor.")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependencia para FastAPI
from sqlalchemy.orm import Session

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

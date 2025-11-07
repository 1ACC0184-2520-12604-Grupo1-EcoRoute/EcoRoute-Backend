from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd
import networkx as nx

import models, schemas, auth
from database import SessionLocal, engine

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="EcoRoute Auth API")

# Configuración de CORS para permitir llamadas desde el frontend
origins = [
    "http://localhost:5173",  # Vite frontend
    "http://127.0.0.1:5173",  # Alternativa
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],         # permitir todos los métodos
    allow_headers=["*"],         # permitir todas las cabeceras
)

# ==============================
# 🔹 Cargar dataset Excel en un grafo
# ==============================
try:
    df = pd.read_excel("data/dataset.xlsx")  # 📌 tu archivo real
except FileNotFoundError:
    raise Exception("⚠️ No se encontró el archivo data/dataset.xlsx")

# Validar columnas necesarias en Excel
required_columns = {"origin", "destination", "total_price"}
if not required_columns.issubset(set(df.columns)):
    raise Exception(f"⚠️ El Excel debe contener las columnas: {required_columns}")

# Crear grafo dirigido con pesos basados en total_price
GRAPH = nx.from_pandas_edgelist(
    df,
    source="origin",
    target="destination",
    edge_attr=True,   # ✅ importante para incluir todos los atributos
    create_using=nx.DiGraph()
)

# ==============================
# Dependencia para manejar sesiones de DB
# ==============================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==============================
# Endpoints de usuarios
# ==============================
@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Usuario ya existe")

    hashed_pw = auth.hash_password(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = auth.create_access_token({"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer"}

# ==============================
# Endpoint de rutas usando Excel
# ==============================
@app.post("/api/compute-route", response_model=schemas.RouteResponse)
def compute_route(req: schemas.RouteRequest):
    origin = req.origin
    dest = req.destination

    if origin not in GRAPH:
        raise HTTPException(status_code=404, detail=f"Origin '{origin}' not found")
    if dest not in GRAPH:
        raise HTTPException(status_code=404, detail=f"Destination '{dest}' not found")

    try:
        # ✅ Usar total_price como peso de la ruta
        path = nx.shortest_path(GRAPH, source=origin, target=dest, weight="total_price")
        total_cost = sum(
            GRAPH[u][v]["total_price"] for u, v in zip(path[:-1], path[1:])
        )
        return {"path": path, "total_cost": total_cost, "details": []}
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="No path found")

# ==============================
# Endpoint de reportes (dummy)
# ==============================
@app.get("/api/reports")
def get_reports():
    reports = [
        {"id": 1, "title": "Reporte de Ventas", "date": "2025-09-01", "status": "Completado"},
        {"id": 2, "title": "Análisis de Mercado", "date": "2025-09-10", "status": "Pendiente"},
        {"id": 3, "title": "Proyección Financiera", "date": "2025-09-15", "status": "Completado"},
    ]
    return {"reports": reports}




# ==============================
# Endpoint de nodos 
# ==============================
@app.get("/api/nodes")
def get_nodes():
    origins = df["origin"].unique().tolist()
    destinations = df["destination"].unique().tolist()
    nodes = sorted(set(origins + destinations))
    return {"nodes": nodes}
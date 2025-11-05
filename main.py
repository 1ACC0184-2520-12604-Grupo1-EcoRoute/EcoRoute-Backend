# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple, Optional
import pandas as pd
import networkx as nx

import models, schemas, auth
from database import SessionLocal, engine

# ==============================
# APP & DB
# ==============================
models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="EcoRoute API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

# ==============================
# Carga/normalización del Excel
# ==============================
try:
    df = pd.read_excel("data/dataset.xlsx")
except FileNotFoundError:
    raise Exception("⚠️ No se encontró el archivo data/dataset.xlsx")

required_columns = {"origin", "destination", "total_price"}
if not required_columns.issubset(set(df.columns)):
    raise Exception(f"⚠️ El Excel debe contener las columnas: {required_columns}")

for col in ("origin", "destination"):
    df[col] = df[col].astype(str).str.strip()

df["total_price"] = pd.to_numeric(df["total_price"], errors="coerce")

# Si falta total_price pero hay quantity+unit_price, se calcula
if {"quantity", "unit_price"}.issubset(df.columns):
    missing = df["total_price"].isna()
    df.loc[missing, "total_price"] = (
        pd.to_numeric(df.loc[missing, "quantity"], errors="coerce") *
        pd.to_numeric(df.loc[missing, "unit_price"], errors="coerce")
    )

# Tarifa (porcentaje) si existe con cualquier nombre común
tariff_col = next((c for c in ["tarifa", "tarifa_pct", "tariff", "tariff_rate", "rate"] if c in df.columns), None)
if tariff_col:
    df["tarifa_pct"] = pd.to_numeric(df[tariff_col], errors="coerce").fillna(0.0)
else:
    df["tarifa_pct"] = 0.0

# Normaliza product si existe
if "product" in df.columns:
    df["product"] = df["product"].astype(str).str.strip()

# Costo efectivo por arista
df["effective_cost"] = df["total_price"] * (1.0 + df["tarifa_pct"] / 100.0)

# Quita filas inválidas
df = df.dropna(subset=["origin", "destination", "effective_cost"])

# Grafo dirigido con todos los atributos
GRAPH = nx.from_pandas_edgelist(
    df, source="origin", target="destination", edge_attr=True, create_using=nx.DiGraph()
)

# ==============================
# Coordenadas base para el mapa
# ==============================
COUNTRY_COORDS: Dict[str, Tuple[float, float]] = {
    "Alemania": (51.1657, 10.4515),
    "Argentina": (-38.4161, -63.6167),
    "Perú": (-9.19, -75.0152),
    "Chile": (-35.6751, -71.5430),
    "Brasil": (-14.2350, -51.9253),
    "Japón": (36.2048, 138.2529),
    "Sudáfrica": (-30.5595, 22.9375),
    "Egipto": (26.8206, 30.8025),
    "China": (35.8617, 104.1954),
    "España": (40.4637, -3.7492),
    "Francia": (46.2276, 2.2137),
    "Italia": (41.8719, 12.5674),
    "México": (23.6345, -102.5528),
    "Estados Unidos": (37.0902, -95.7129),
    "India": (20.5937, 78.9629),
    "Australia": (-25.2744, 133.7751),
}

# ==============================
# Pydantic models
# ==============================
class GeoPoint(BaseModel):
    name: str
    lat: float
    lng: float

class RouteGeoResponse(BaseModel):
    path: List[str]
    cost: float
    geoPath: List[GeoPoint]

class NodesResponse(BaseModel):
    nodes: List[str]
    geo: Dict[str, Tuple[float, float]]

class RouteComputeBody(BaseModel):
    origin: str
    destination: str
    product: Optional[str] = None

# ==============================
# Dependencia DB
# ==============================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==============================
# Auth (igual que tenías)
# ==============================
@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    hashed_pw = auth.hash_password(user.password)
    new_user = models.User(username=user.username, email=user.email, hashed_password=hashed_pw)
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
# Lógica de rutas
# ==============================
def _edge_cost(u, v) -> float:
    """Costo efectivo = total_price * (1 + tarifa_pct/100)."""
    data = GRAPH[u][v]
    eff = data.get("effective_cost")
    if eff is not None:
        return float(eff)
    total_price = float(data.get("total_price", 0.0))
    tarifa_pct = float(data.get("tarifa_pct", 0.0))
    return total_price * (1.0 + tarifa_pct / 100.0)

def shortest_path_with_cost(origin: str, dest: str, product: Optional[str] = None) -> Tuple[List[str], float]:
    """Devuelve (path, total_cost). Si hay 'product', filtra aristas por ese producto exacto (case-insensitive)."""
    if origin not in GRAPH:
        raise HTTPException(status_code=404, detail=f"Origin '{origin}' not found")
    if dest not in GRAPH:
        raise HTTPException(status_code=404, detail=f"Destination '{dest}' not found")

    G = GRAPH
    if "product" in df.columns and product:
        p = str(product).strip().lower()
        edges = [(u, v) for u, v, d in GRAPH.edges(data=True) if str(d.get("product", "")).strip().lower() == p]
        if not edges:
            raise HTTPException(status_code=404, detail=f"No hay aristas para el producto '{product}'.")
        G = nx.DiGraph()
        G.add_nodes_from(GRAPH.nodes())
        for u, v in edges:
            G.add_edge(u, v, **GRAPH[u][v])

    try:
        path = nx.shortest_path(G, source=origin, target=dest, weight=lambda u, v, d: _edge_cost(u, v))
        total_cost = sum(_edge_cost(u, v) for u, v in zip(path[:-1], path[1:]))
        return path, float(total_cost)
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="No path found")

def to_geo_path(path: List[str]) -> List[GeoPoint]:
    geo = []
    for name in path:
        if name not in COUNTRY_COORDS:
            raise HTTPException(status_code=400, detail=f"Missing coordinates for '{name}'")
        lat, lng = COUNTRY_COORDS[name]
        geo.append(GeoPoint(name=name, lat=lat, lng=lng))
    return geo

# ==============================
# Endpoints de rutas (compatibles)
# ==============================
# 1) Simple legacy
@app.post("/api/compute-route", response_model=schemas.RouteResponse)
def compute_route(req: schemas.RouteRequest):
    path, total_cost = shortest_path_with_cost(req.origin, req.destination, getattr(req, "product", None))
    return {"path": path, "total_cost": total_cost, "details": []}

# 2) GET con geo (legacy)
@app.get("/api/route", response_model=RouteGeoResponse)
def route_with_geo_get(origin: str, destination: str, product: Optional[str] = None):
    path, total_cost = shortest_path_with_cost(origin, destination, product)
    geo_path = to_geo_path(path)
    return RouteGeoResponse(path=path, cost=total_cost, geoPath=geo_path)

# 3) NUEVO: POST /api/route/compute (con y sin slash)
@app.post("/api/route/compute", response_model=RouteGeoResponse)
@app.post("/api/route/compute/", response_model=RouteGeoResponse)
def route_with_geo_post(body: RouteComputeBody):
    path, total_cost = shortest_path_with_cost(body.origin, body.destination, body.product)
    geo_path = to_geo_path(path)
    return RouteGeoResponse(path=path, cost=total_cost, geoPath=geo_path)

# 4) Alias opcional: POST /api/route
@app.post("/api/route", response_model=RouteGeoResponse)
def route_with_geo_post_alias(body: RouteComputeBody):
    path, total_cost = shortest_path_with_cost(body.origin, body.destination, body.product)
    geo_path = to_geo_path(path)
    return RouteGeoResponse(path=path, cost=total_cost, geoPath=geo_path)

# ==============================
# Nodos y reportes
# ==============================
@app.get("/api/nodes", response_model=NodesResponse)
def get_nodes():
    origins = df["origin"].astype(str).str.strip().unique().tolist()
    destinations = df["destination"].astype(str).str.strip().unique().tolist()
    nodes = sorted(set(origins + destinations))
    geo_filtered = {k: v for k, v in COUNTRY_COORDS.items() if k in nodes}
    return NodesResponse(nodes=nodes, geo=geo_filtered)

@app.get("/api/reports")
def get_reports():
    # Entrega en DOS formatos para compatibilidad: array "reports" y "items"
    reports = [
        {"id": 1, "title": "Reporte de Rutas", "date": "2025-11-01", "status": "Completado"},
        {"id": 2, "title": "Análisis de Costos", "date": "2025-11-02", "status": "Pendiente"},
        {"id": 3, "title": "Rutas Más Optimizadas", "date": "2025-11-03", "status": "Completado"},
    ]
    return {"reports": reports, "items": reports}

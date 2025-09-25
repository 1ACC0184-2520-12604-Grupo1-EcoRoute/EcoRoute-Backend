from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models, schemas, auth
from database import SessionLocal, engine
from data_loader import GRAPH
import networkx as nx

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="EcoRoute Auth API")

# Configuración de CORS para permitir llamadas desde el frontend
origins = [
    "http://localhost:5173",  # Vite frontend
    "http://127.0.0.1:5173",  # Alternativa por si usas esta URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],         # permitir todos los métodos
    allow_headers=["*"],         # permitir todas las cabeceras
)

# Dependencia para manejar sesiones de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint para registrar usuario
@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Verificar si el usuario ya existe
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

# Endpoint para login de usuario
@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = auth.create_access_token({"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/compute-route", response_model=schemas.RouteResponse)
def compute_route(req: schemas.RouteRequest):
    origin = req.origin
    dest = req.destination
    product = req.product

    if origin not in GRAPH:
        raise HTTPException(status_code=404, detail=f"Origin '{origin}' not found")
    if dest not in GRAPH:
        raise HTTPException(status_code=404, detail=f"Destination '{dest}' not found")

    try:
        path = nx.shortest_path(GRAPH, source=origin, target=dest, weight="weight")
        total_cost = sum(
            GRAPH[u][v]["weight"] for u, v in zip(path[:-1], path[1:])
        )
        return {"path": path, "total_cost": total_cost, "details": []}
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="No path found")

# endpoint de reportes
@app.get("/api/reports")
def get_reports():
    # retorno de reportes como ejemplo
    reports = [
        {"id": 1, "title": "Reporte de Ventas", "date": "2025-09-01", "status": "Completado"},
        {"id": 2, "title": "Análisis de Mercado", "date": "2025-09-10", "status": "Pendiente"},
        {"id": 3, "title": "Proyección Financiera", "date": "2025-09-15", "status": "Completado"},
    ]
    return {"reports": reports}
from app.database import get_db
from app.models.grafo import GrafoRutas
from app.models.pais_model import PaisModel
from app.services.rutas_service import RutasService
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session


router = APIRouter(tags=["Rutas"])


class RutaRequest(BaseModel):
    algoritmo: str      # "dijkstra" o "floyd-warshall"
    criterio: str       # "rapidez" o "economia"
    origen: str
    destino: str
    producto_id: Optional[str] = None


class RutaResponse(BaseModel):
    ruta: List[str]
    tipo_ruta: str
    distancia_total: float
    tiempo_total: float
    costo_total: float


@router.post("/ruta-optima", response_model=RutaResponse)
async def ruta_optima(req: RutaRequest, db: Session = Depends(get_db)):
    if req.origen == req.destino:
        raise HTTPException(status_code=400, detail="Origen y destino no pueden ser iguales.")

    grafo = GrafoRutas()
    grafo.cargar_desde_bd(db)   # ← AHORA CARGA TODO DE AIVEN

    service = RutasService(grafo)

    resultado = service.calcular_ruta_optima(
        algoritmo=req.algoritmo,
        criterio=req.criterio,
        origen=req.origen,
        destino=req.destino,
        producto_id=req.producto_id
    )

    return resultado


@router.get("/api/nodes")
def get_nodes(db: Session = Depends(get_db)):
    paises = db.query(PaisModel).all()

    nodes = [p.id for p in paises]
    geo = {p.id: [p.lat, p.lon] for p in paises}

    return {"nodes": nodes, "geo": geo}

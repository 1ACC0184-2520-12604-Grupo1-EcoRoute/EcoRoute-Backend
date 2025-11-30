from app.database import get_db
from app.models.grafo import GrafoRutas
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


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

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
def ruta_optima(req: RutaRequest):
    if req.origen == req.destino:
        raise HTTPException(status_code=400, detail="Origen y destino no pueden ser iguales.")

    # Demo
    return RutaResponse(
        ruta=[req.origen, req.destino],
        tipo_ruta="aerea",
        distancia_total=17000,
        tiempo_total=22,
        costo_total=1500,
    )
@router.get("/api/nodes")
def get_nodes():
    return {
        "nodes": ["PER", "CHL", "BRA", "USA", "CHN"],
        "geo": {
            "PER": [-12.0464, -77.0428],
            "CHL": [-33.4489, -70.6693],
            "BRA": [-15.7801, -47.9292],
            "USA": [37.0902, -95.7129],
            "CHN": [35.8617, 104.1954],
        },
    }

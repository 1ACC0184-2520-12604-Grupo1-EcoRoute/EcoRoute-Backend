from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class RutaOptimaRequest(BaseModel):
    algoritmo: Literal["dijkstra", "floyd-warshall"]
    criterio: Literal["rapidez", "economia"]
    origen: str = Field(..., description="ID de país origen, ej. PER")
    destino: str = Field(..., description="ID de país destino, ej. CHN")
    producto_id: Optional[str] = Field(
        None,
        description="ID del producto a transportar (opcional). Ej: SOLAR_PANEL_STD"
    )


class RutaOptimaResponse(BaseModel):
    ruta: List[str]
    tipo_ruta: Literal["aerea", "terrestre", "maritima", "mixta"]
    distancia_total: float
    tiempo_total: float
    costo_total: float

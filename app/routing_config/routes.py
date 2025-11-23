from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List, Literal
import json

from app.core.security import get_current_user

router = APIRouter(tags=["GraphConfig"])

# Archivo donde guardamos el grafo personalizado
CUSTOM_GRAPH_PATH = Path("app/data/custom_graph.json")


class CustomNode(BaseModel):
    id: str = Field(..., description="ID del país/nodo, ej. PER, DEU, etc.")
    nombre: str = Field(..., description="Nombre legible")
    lat: float
    lon: float


class CustomRoute(BaseModel):
    origen: str
    destino: str
    tipo: Literal["aerea", "maritima", "terrestre", "mixta"]
    distancia_km: float
    tiempo_horas: float
    costo_base_usd_ton: float


class GraphConfig(BaseModel):
    nodos: List[CustomNode] = []
    rutas: List[CustomRoute] = []


def _load_config() -> GraphConfig:
    if not CUSTOM_GRAPH_PATH.exists():
        return GraphConfig(nodos=[], rutas=[])
    try:
        with CUSTOM_GRAPH_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return GraphConfig(**data)
    except Exception:
        # Si está roto el json, lo reiniciamos
        return GraphConfig(nodos=[], rutas=[])


def _save_config(cfg: GraphConfig) -> None:
    CUSTOM_GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CUSTOM_GRAPH_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg.dict(), f, ensure_ascii=False, indent=2)


@router.get("/graph-config/me", response_model=GraphConfig)
def get_my_graph_config(user=Depends(get_current_user)):
    """
    Devuelve los nodos/rutas personalizados para el grafo de Dijkstra/Floyd.
    (Por ahora es global, pero solo accesible autenticado).
    """
    return _load_config()


@router.post("/graph-config/me/node", response_model=GraphConfig)
def add_custom_node(node: CustomNode, user=Depends(get_current_user)):
    """
    Agrega o actualiza un nodo.
    """
    cfg = _load_config()

    # upsert por id
    cfg.nodos = [n for n in cfg.nodos if n.id != node.id]
    cfg.nodos.append(node)

    _save_config(cfg)
    return cfg


@router.post("/graph-config/me/route", response_model=GraphConfig)
def add_custom_route(route: CustomRoute, user=Depends(get_current_user)):
    """
    Agrega una ruta. El origen y destino deben ser distintos.
    """
    if route.origen == route.destino:
        raise HTTPException(
            status_code=400,
            detail="Origen y destino no pueden ser iguales.",
        )

    cfg = _load_config()
    cfg.rutas.append(route)
    _save_config(cfg)
    return cfg


@router.delete("/graph-config/me/reset", response_model=GraphConfig)
def reset_my_graph_config(user=Depends(get_current_user)):
    """
    Limpia TODAS las personalizaciones del grafo.
    """
    cfg = GraphConfig(nodos=[], rutas=[])
    _save_config(cfg)
    return cfg

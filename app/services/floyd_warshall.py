from typing import Dict, List, Tuple, Optional, Callable
from app.models.grafo import GrafoRutas
from app.models.ruta import Ruta


def floyd_warshall(
    grafo: GrafoRutas,
    weight_func: Callable[[Ruta], float],
) -> Tuple[Dict[Tuple[str, str], float], Dict[Tuple[str, str], Optional[str]]]:
    nodos = grafo.obtener_nodos()
    dist: Dict[Tuple[str, str], float] = {}
    next_hop: Dict[Tuple[str, str], Optional[str]] = {}

    for i in nodos:
        for j in nodos:
            if i == j:
                dist[(i, j)] = 0.0
                next_hop[(i, j)] = j
            else:
                dist[(i, j)] = float("inf")
                next_hop[(i, j)] = None

    for i in nodos:
        for ruta in grafo.vecinos(i):
            w = weight_func(ruta)
            if w < dist[(ruta.origen, ruta.destino)]:
                dist[(ruta.origen, ruta.destino)] = w
                next_hop[(ruta.origen, ruta.destino)] = ruta.destino

    for k in nodos:
        for i in nodos:
            for j in nodos:
                if dist[(i, k)] + dist[(k, j)] < dist[(i, j)]:
                    dist[(i, j)] = dist[(i, k)] + dist[(k, j)]
                    next_hop[(i, j)] = next_hop[(i, k)]

    return dist, next_hop


def reconstruir_ruta_floyd(
    origen: str,
    destino: str,
    grafo: GrafoRutas,
    next_hop: Dict[Tuple[str, str], Optional[str]],
    weight_func: Callable[[Ruta], float],
) -> Optional[List[Ruta]]:
    if next_hop.get((origen, destino)) is None:
        return None

    ruta_completa: List[Ruta] = []
    actual = origen
    while actual != destino:
        siguiente = next_hop.get((actual, destino))
        if siguiente is None:
            return None

        candidatos = [r for r in grafo.vecinos(actual) if r.destino == siguiente]
        if not candidatos:
            return None

        mejor = min(candidatos, key=weight_func)
        if weight_func(mejor) == float("inf"):
            return None

        ruta_completa.append(mejor)
        actual = siguiente

    return ruta_completa

import heapq
from typing import Dict, List, Tuple, Optional, Callable
from app.models.grafo import GrafoRutas
from app.models.ruta import Ruta


def dijkstra(
    grafo: GrafoRutas,
    origen: str,
    destino: str,
    weight_func: Callable[[Ruta], float],
) -> Optional[Tuple[List[Ruta], float]]:
    dist: Dict[str, float] = {n: float("inf") for n in grafo.obtener_nodos()}
    previo: Dict[str, Tuple[str, Ruta]] = {}

    dist[origen] = 0.0
    pq: List[Tuple[float, str]] = [(0.0, origen)]

    while pq:
        dist_actual, nodo_actual = heapq.heappop(pq)
        if dist_actual > dist[nodo_actual]:
            continue
        if nodo_actual == destino:
            break

        for ruta in grafo.vecinos(nodo_actual):
            w = weight_func(ruta)
            if w == float("inf"):
                continue
            nuevo = dist_actual + w
            if nuevo < dist[ruta.destino]:
                dist[ruta.destino] = nuevo
                previo[ruta.destino] = (nodo_actual, ruta)
                heapq.heappush(pq, (nuevo, ruta.destino))

    if dist[destino] == float("inf"):
        return None

    rutas_resultado: List[Ruta] = []
    actual = destino
    while actual != origen:
        anterior, ruta_usada = previo[actual]
        rutas_resultado.append(ruta_usada)
        actual = anterior

    rutas_resultado.reverse()
    return rutas_resultado, dist[destino]

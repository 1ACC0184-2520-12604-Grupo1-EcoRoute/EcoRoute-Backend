from typing import Optional, List, Callable
from app.models.grafo import GrafoRutas
from app.models.ruta import Ruta
from app.models.producto import Producto
from .dijkstra import dijkstra
from .floyd_warshall import floyd_warshall, reconstruir_ruta_floyd


class RutaNoEncontrada(Exception):
    pass


class PaisInvalido(Exception):
    pass


class ProductoInvalido(Exception):
    pass


class RutasService:
    def __init__(self, grafo: GrafoRutas):
        self.grafo = grafo
        self._fw_cache = {}  # cache por clave de peso

    def _mapear_criterio(self, criterio: str) -> str:
        if criterio in ("rapidez", "economia"):
            return criterio
        raise ValueError("Criterio no válido (use 'rapidez' o 'economia').")

    def _build_weight_func(
        self,
        criterio: str,
        producto: Optional[Producto],
    ) -> Callable[[Ruta], float]:
        if criterio == "rapidez":
            # Optimizar por tiempo, independiente del producto
            def wf(r: Ruta) -> float:
                # Si el producto no puede ir por este tipo de ruta, la descartamos
                if producto and r.tipo not in producto.tipo_transporte_permitido:
                    return float("inf")
                return r.tiempo_horas
            return wf

        if criterio == "economia":
            def wf(r: Ruta) -> float:
                if producto and r.tipo not in producto.tipo_transporte_permitido:
                    return float("inf")
                # Si hay producto: costo proporcional al peso
                if producto:
                    return r.costo_base_usd_ton * (producto.peso_kg / 1000.0)
                # Si no hay producto: usamos costo base como referencia
                return r.costo_base_usd_ton
            return wf

        raise ValueError("Criterio desconocido.")

    def calcular_ruta_optima(
        self,
        algoritmo: str,
        criterio: str,
        origen: str,
        destino: str,
        producto_id: Optional[str] = None,
    ):
        if not self.grafo.validar_pais(origen):
            raise PaisInvalido(f"El país de origen '{origen}' no existe.")
        if not self.grafo.validar_pais(destino):
            raise PaisInvalido(f"El país de destino '{destino}' no existe.")
        if origen == destino:
            raise RutaNoEncontrada("El origen y destino no pueden ser el mismo.")

        criterio_norm = self._mapear_criterio(criterio)

        producto: Optional[Producto] = None
        if producto_id:
            producto = self.grafo.obtener_producto(producto_id)
            if not producto:
                raise ProductoInvalido(f"El producto '{producto_id}' no existe.")

        weight_func = self._build_weight_func(criterio_norm, producto)

        if algoritmo == "dijkstra":
            resultado = dijkstra(self.grafo, origen, destino, weight_func)
            if resultado is None:
                raise RutaNoEncontrada("No existe una ruta disponible para los parámetros seleccionados.")
            rutas, _ = resultado

        elif algoritmo == "floyd-warshall":
            cache_key = (criterio_norm, producto_id or "no_product")
            if cache_key not in self._fw_cache:
             dist, next_hop, edge_used = floyd_warshall(self.grafo, weight_func)
             self._fw_cache[cache_key] = (dist, next_hop, edge_used)
             _, next_hop, edge_used = self._fw_cache[cache_key]
             rutas = reconstruir_ruta_floyd(origen, destino, self.grafo, next_hop, edge_used, weight_func)
            if rutas is None:
                raise RutaNoEncontrada("No existe una ruta disponible para los parámetros seleccionados.")
        else:
            raise ValueError("Algoritmo no válido (use 'dijkstra' o 'floyd-warshall').")

        return self._agregar_resumen_ruta(rutas, criterio_norm, producto)

    def _agregar_resumen_ruta(
        self,
        rutas: List[Ruta],
        criterio: str,
        producto: Optional[Producto],
    ):
        distancia_total = sum(r.distancia_km for r in rutas)
        tiempo_total = sum(r.tiempo_horas for r in rutas)

        if criterio == "economia":
            weight_func = self._build_weight_func("economia", producto)
            costo_total = sum(weight_func(r) for r in rutas)
        else:
            # Si no optimizamos por economía, igual calculamos un costo aproximado:
            weight_func = self._build_weight_func("economia", producto)
            costo_total = sum(weight_func(r) for r in rutas)

        ruta_ids = [rutas[0].origen] + [r.destino for r in rutas]
        tipo_ruta = self._determinar_tipo_ruta(rutas)

        return {
            "ruta": ruta_ids,
            "tipo_ruta": tipo_ruta,
            "distancia_total": round(distancia_total, 2),
            "tiempo_total": round(tiempo_total, 2),
            "costo_total": round(costo_total, 2),
        }

    def _determinar_tipo_ruta(self, rutas: List[Ruta]) -> str:
        tipos = {r.tipo for r in rutas}
        if len(tipos) == 1:
            unico = tipos.pop()
            if unico in {"aerea", "maritima", "terrestre"}:
                return unico
        return "mixta"

import json
import os
from typing import Dict, List
from .nodo import Nodo
from .ruta import Ruta
from .producto import Producto
from sqlalchemy import select
from app.models.ruta_model import RutaModel
from app.models.pais_model import PaisModel


class GrafoRutas:

    def __init__(self):
        self.nodos: Dict[str, Nodo] = {}
        self.adyacencia: Dict[str, List[Ruta]] = {}
        self.productos: Dict[str, Producto] = {}

    def cargar_desde_bd(self, db):
        self.nodos = {}
        self.adyacencia = {}
        self.productos = {}

        # 1. Cargar países
        paises = db.execute(select(PaisModel)).scalars().all()
        for p in paises:
            self.nodos[p.id] = Nodo(
                id=p.id,
                nombre=p.nombre,
                lat=p.lat,
                lon=p.lon
            )
            self.adyacencia[p.id] = []   # correcta indentación

        # 2. Cargar rutas
        rutas = db.execute(select(RutaModel)).scalars().all()
        for r in rutas:

            # nodos faltantes
            if r.origen_id not in self.nodos:
                self.nodos[r.origen_id] = Nodo(r.origen_id, r.origen_id, 0, 0)
                self.adyacencia[r.origen_id] = []

            if r.destino_id not in self.nodos:
                self.nodos[r.destino_id] = Nodo(r.destino_id, r.destino_id, 0, 0)
                self.adyacencia[r.destino_id] = []

            ruta = Ruta(
                origen=r.origen_id,
                destino=r.destino_id,
                tipo=r.tipo,
                distancia_km=r.distancia_km,
                tiempo_horas=r.tiempo_horas,
                costo_base_usd_ton=r.costo_base_usd_ton,
            )

            self.adyacencia[r.origen_id].append(ruta)

    # ------------------------------
    # JSON loader (si aplicara)
    # ------------------------------

    def cargar_desde_json(self, ruta_archivo: str):
        if not os.path.exists(ruta_archivo):
            raise FileNotFoundError(f"No se encontró el archivo de datos: {ruta_archivo}")

        with open(ruta_archivo, "r", encoding="utf-8") as f:
            data = json.load(f)

        for p in data.get("paises", []):
            nodo = Nodo(
                id=p["id"],
                nombre=p["nombre"],
                lat=p["lat"],
                lon=p["lon"],
            )
            self.nodos[nodo.id] = nodo
            if nodo.id not in self.adyacencia:
                self.adyacencia[nodo.id] = []

        for pr in data.get("productos", []):
            producto = Producto(
                id=pr["id"],
                nombre=pr["nombre"],
                categoria=pr["categoria"],
                peso_kg=float(pr["peso_kg"]),
                volumen_m3=float(pr["volumen_m3"]),
                precio_unitario_usd=float(pr["precio_unitario_usd"]),
                tipo_transporte_permitido=pr["tipo_transporte_permitido"],
            )
            self.productos[producto.id] = producto

        for r in data.get("rutas", []):
            ruta = Ruta(
                origen=r["origen"],
                destino=r["destino"],
                tipo=r["tipo"],
                distancia_km=float(r["distancia_km"]),
                tiempo_horas=float(r["tiempo_horas"]),
                costo_base_usd_ton=float(r["costo_base_usd_ton"]),
            )
            if ruta.origen not in self.adyacencia:
                self.adyacencia[ruta.origen] = []
            self.adyacencia[ruta.origen].append(ruta)

    # Helpers

    def vecinos(self, nodo_id: str) -> List[Ruta]:
        return self.adyacencia.get(nodo_id, [])

    def validar_pais(self, pais_id: str) -> bool:
        return pais_id in self.nodos

    def obtener_nodos(self) -> List[str]:
        return list(self.nodos.keys())

    def obtener_producto(self, producto_id: str) -> Producto | None:
        return self.productos.get(producto_id)

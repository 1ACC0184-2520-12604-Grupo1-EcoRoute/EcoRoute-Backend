from dataclasses import dataclass

@dataclass
class Ruta:
    origen: str
    destino: str
    tipo: str                    # "aerea" | "maritima" | "terrestre" | "mixta"
    distancia_km: float
    tiempo_horas: float
    costo_base_usd_ton: float    # Costo base por tonelada en este tramo

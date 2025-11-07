from dataclasses import dataclass
from typing import List

@dataclass
class Producto:
    id: str                      # Ej: "SOLAR_PANEL_STD"
    nombre: str                  # Ej: "Panel solar 450W"
    categoria: str               # Ej: "energia_solar"
    peso_kg: float               # Peso por unidad
    volumen_m3: float            # Volumen por unidad
    precio_unitario_usd: float   # Precio del producto
    tipo_transporte_permitido: List[str]  # ["aerea","maritima","terrestre","mixta"]

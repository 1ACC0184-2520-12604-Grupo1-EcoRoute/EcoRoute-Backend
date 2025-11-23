from dataclasses import dataclass

@dataclass
class Nodo:
    id: str        # Código del país, ej. "PER"
    nombre: str
    lat: float
    lon: float

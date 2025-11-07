# schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Dict, Tuple, List

# ========= Usuarios =========
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

# ========= Nodos / Rutas =========
class NodesResponse(BaseModel):
    nodes: List[str]
    geo: Dict[str, Tuple[float, float]]

class RouteComputeRequest(BaseModel):
    origin: str
    destination: str
    product: str

class RouteGeoPoint(BaseModel):
    name: str
    lat: float
    lng: float

class RouteGeoResponse(BaseModel):
    path: List[str]
    cost: float
    geoPath: List[RouteGeoPoint]

# ========= Reportes =========
class ReportOut(BaseModel):
    id: int
    created_at: datetime
    user_id: int
    origin: str
    destination: str
    product: str
    cost: float
    path: str           # almacenado como JSON string en BD
    algorithm: str

    model_config = ConfigDict(from_attributes=True)

from typing import List
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True



class RouteRequest(BaseModel):
    origin: str
    destination: str
    product: str = "Paneles solares"

class RouteResponse(BaseModel):
    path: List[str]
    total_cost: float
    details: List[dict]  # list of edge details (origin,dest,weight,tariff,shipping,product)

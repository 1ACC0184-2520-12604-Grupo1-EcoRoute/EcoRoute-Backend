from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import distinct
import unicodedata

from app.database import get_db
from app.models.trade_data import TradeData

router = APIRouter(tags=["TradeFlows"])

# --- TU DICCIONARIO DE COORDENADAS (Mantenlo igual) ---
COUNTRY_COORDS = {
    "alemania": (51.1657, 10.4515),
    "germany": (51.1657, 10.4515),
    "china": (35.8617, 104.1954),
    "brasil": (-14.2350, -51.9253),
    "brazil": (-14.2350, -51.9253),
    "japon": (36.2048, 138.2529),
    "japan": (36.2048, 138.2529),
    "espana": (40.4637, -3.7492),
    "spain": (40.4637, -3.7492),
    "francia": (46.6034, 1.8883),
    "france": (46.6034, 1.8883),
    "corea del sur": (35.9078, 127.7669),
    "south korea": (35.9078, 127.7669),
    "mexico": (23.6345, -102.5528),
    "eeuu": (37.0902, -95.7129),
    "estados unidos": (37.0902, -95.7129),
    "usa": (37.0902, -95.7129),
    "united states": (37.0902, -95.7129),
    "india": (20.5937, 78.9629),
    "sudafrica": (-30.5595, 22.9375),
    "south africa": (-30.5595, 22.9375),
    "peru": (-9.19, -75.0152),
    "chile": (-35.6751, -71.5430),
    "egipto": (26.8206, 30.8025),
    "egypt": (26.8206, 30.8025),
    "colombia": (4.5709, -74.2973),
    "vietnam": (14.0583, 108.2772),
    "argentina": (-38.4161, -63.6167),
    "republica argentina": (-38.4161, -63.6167),
    "rep argentina": (-38.4161, -63.6167),
}

def normalize_country(name: str) -> str:
    if not name: return ""
    s = str(name).strip().replace(".", "")
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.lower()

def get_coords(country_name):
    key = normalize_country(country_name)
    return COUNTRY_COORDS.get(key, (None, None))


# --- ENDPOINT 1: OPTIMIZADO PARA SELECTORES ---
# Solo devuelve listas de valores únicos, no toda la data.
@router.get("/api/trade-options")
def get_trade_options(db: Session = Depends(get_db)):
    """
    Devuelve listas únicas de orígenes, destinos y productos para llenar los dropdowns del frontend.
    Mucho más rápido que traer 5000 filas.
    """
    try:
        # Consultas optimizadas con DISTINCT
        origins = db.query(distinct(TradeData.origin)).filter(TradeData.origin.isnot(None)).all()
        destinations = db.query(distinct(TradeData.destination)).filter(TradeData.destination.isnot(None)).all()
        products = db.query(distinct(TradeData.product)).filter(TradeData.product.isnot(None)).all()
        
        return {
            "origins": sorted([r[0] for r in origins if r[0]]),
            "destinations": sorted([r[0] for r in destinations if r[0]]),
            "products": sorted([r[0] for r in products if r[0]])
        }
    except Exception as e:
        print(f"Error fetching options: {e}")
        return {"origins": [], "destinations": [], "products": []}


# --- ENDPOINT 2: DETALLE DE FLUJO ESPECÍFICO ---
# Busca solo lo que el usuario seleccionó.
@router.get("/api/trade-flow-detail")
def get_trade_flow_detail(
    origin: str = Query(..., description="País de origen"),
    destination: str = Query(..., description="País de destino"),
    product: str = Query(..., description="Nombre del producto"),
    db: Session = Depends(get_db)
):
    """
    Busca un registro específico basado en los filtros.
    Eficiente porque filtra en SQL antes de traer datos a memoria.
    """
    # Buscamos el registro exacto
    flow = db.query(TradeData).filter(
        TradeData.origin == origin,
        TradeData.destination == destination,
        TradeData.product == product
    ).first()

    if not flow:
        # Si no existe exacto, intentamos buscar algo similar (opcional)
        raise HTTPException(status_code=404, detail="No se encontraron datos comerciales para esta ruta y producto.")

    # Calculamos coordenadas
    orig_lat, orig_lng = get_coords(flow.origin)
    dest_lat, dest_lng = get_coords(flow.destination)

    return {
        "origin": flow.origin,
        "destination": flow.destination,
        "product": flow.product,
        "quantity": float(flow.quantity or 0),
        "unit_price": float(flow.unit_price or 0),
        "tariff": float(flow.tariff or 0),
        "total_price": float(flow.total_price or 0),
        "date": str(flow.date) if flow.date else None,
        # Coordenadas para el mapa
        "origin_lat": orig_lat,
        "origin_lng": orig_lng,
        "destination_lat": dest_lat,
        "destination_lng": dest_lng,
    }

# --- ENDPOINT 3: BACKWARDS COMPATIBILITY (Opcional) ---
# Mantenemos este si necesitas traer "todo" para Kruskal/TSP global, pero limitamos a 500
@router.get("/api/trade-flows")
def get_all_trade_flows(limit: int = 500, db: Session = Depends(get_db)):
    """
    Trae una muestra de flujos (máximo 500) para visualización general o algoritmos de red.
    """
    rows = db.query(TradeData).limit(limit).all()
    flows = []
    
    for row in rows:
        o_lat, o_lng = get_coords(row.origin)
        d_lat, d_lng = get_coords(row.destination)
        
        # Solo agregamos si tenemos coordenadas (útil para el mapa)
        if o_lat and d_lat:
            flows.append({
                "origin": row.origin,
                "destination": row.destination,
                "product": row.product,
                "total_price": float(row.total_price or 0),
                "origin_lat": o_lat,
                "origin_lng": o_lng,
                "destination_lat": d_lat,
                "destination_lng": d_lng,
                "tariff": float(row.tariff or 0)
            })
            
    return {"flows": flows}

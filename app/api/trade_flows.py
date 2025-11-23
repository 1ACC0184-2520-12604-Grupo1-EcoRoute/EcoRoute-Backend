from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import unicodedata

from app.database import get_db
from app.models.trade_data import TradeData

router = APIRouter(tags=["TradeFlows"])


def normalize_country(name: str) -> str:
    """
    Normaliza nombres de países:
    - quita espacios extremos
    - quita puntos
    - elimina acentos
    - pasa a minúsculas
    """
    if not name:
        return ""
    s = str(name).strip()
    s = s.replace(".", "")
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.lower()


# Diccionario usando nombres NORMALIZADOS como llaves
COUNTRY_COORDS = {
    # Alemania / Germany
    "alemania": (51.1657, 10.4515),
    "germany": (51.1657, 10.4515),

    # China
    "china": (35.8617, 104.1954),

    # Brasil / Brazil
    "brasil": (-14.2350, -51.9253),
    "brazil": (-14.2350, -51.9253),

    # Japón / Japan
    "japon": (36.2048, 138.2529),
    "japan": (36.2048, 138.2529),

    # España / Spain
    "espana": (40.4637, -3.7492),
    "spain": (40.4637, -3.7492),

    # Francia / France
    "francia": (46.6034, 1.8883),
    "france": (46.6034, 1.8883),

    # Corea del Sur / South Korea
    "corea del sur": (35.9078, 127.7669),
    "south korea": (35.9078, 127.7669),

    # México / Mexico
    "mexico": (23.6345, -102.5528),

    # Estados Unidos / USA / EE.UU.
    "eeuu": (37.0902, -95.7129),
    "estados unidos": (37.0902, -95.7129),
    "usa": (37.0902, -95.7129),
    "united states": (37.0902, -95.7129),

    # India
    "india": (20.5937, 78.9629),

    # Sudáfrica / South Africa
    "sudafrica": (-30.5595, 22.9375),
    "south africa": (-30.5595, 22.9375),

    # Perú / Peru
    "peru": (-9.19, -75.0152),

    # Chile
    "chile": (-35.6751, -71.5430),

    # Egipto / Egypt
    "egipto": (26.8206, 30.8025),
    "egypt": (26.8206, 30.8025),

    # Colombia
    "colombia": (4.5709, -74.2973),

    # Vietnam
    "vietnam": (14.0583, 108.2772),

    # Argentina
    "argentina": (-38.4161, -63.6167),
    "republica argentina": (-38.4161, -63.6167),
    "rep argentina": (-38.4161, -63.6167),
}


@router.get("/api/trade-flows")
def get_trade_flows(db: Session = Depends(get_db)):
    """
    Lee TODA la tabla trade_data desde MySQL Aiven.
    Devuelve cada flujo con coordenadas si existen en COUNTRY_COORDS.
    """
    rows = db.query(TradeData).all()
    if not rows:
        # No es error grave, pero puede ayudar al front a mostrar mensaje
        return {"flows": []}

    flows = []

    for row in rows:
        origin = row.origin
        destination = row.destination

        origin_key = normalize_country(origin)
        dest_key = normalize_country(destination)

        origin_coords = COUNTRY_COORDS.get(origin_key)
        dest_coords = COUNTRY_COORDS.get(dest_key)

        flow = {
            "origin": origin,
            "destination": destination,
            "product": row.product,
            "quantity": float(row.quantity) if row.quantity is not None else 0.0,
            "unit_price": float(row.unit_price) if row.unit_price is not None else 0.0,
            "tariff": float(row.tariff) if row.tariff is not None else 0.0,
            "date": str(row.date) if row.date is not None else None,
            "total_price": float(row.total_price) if row.total_price is not None else 0.0,
            "origin_lat": origin_coords[0] if origin_coords else None,
            "origin_lng": origin_coords[1] if origin_coords else None,
            "destination_lat": dest_coords[0] if dest_coords else None,
            "destination_lng": dest_coords[1] if dest_coords else None,
        }

        flows.append(flow)

    return {"flows": flows}

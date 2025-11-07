from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd
import unicodedata

router = APIRouter(tags=["TradeFlows"])

# Ruta al dataset
DATASET_PATH = Path("app/data/dataset.xlsx")


def normalize_country(name: str) -> str:
    """
    Normaliza nombres de países para matchear:
    - Quita espacios extremos
    - Quita puntos
    - Elimina acentos
    - Pasa a minúsculas
    Ej: 'Brasil', 'BRASIL ', 'Brazil', 'México', 'EE.UU.' -> brasil, brazil, mexico, eeuu
    """
    if not name:
        return ""
    s = str(name).strip()
    s = s.replace(".", "")
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s.lower()


# Diccionario usando nombres normalizados como llaves
COUNTRY_COORDS = {
    # Alemania / Germany
    "alemania": (51.1657, 10.4515),
    "Alemania": (51.1657, 10.4515),
    "germany": (51.1657, 10.4515),
    "Germany": (51.1657, 10.4515),

    # China
    "china": (35.8617, 104.1954),
    "China": (35.8617, 104.1954),

    # Brasil / Brazil
    "brasil": (-14.2350, -51.9253),
    "Brasil": (-14.2350, -51.9253),
    "brazil": (-14.2350, -51.9253),
    "Brazil": (-14.2350, -51.9253),

    # Japón / Japan
    "japon": (36.2048, 138.2529),
    "Japón": (36.2048, 138.2529),
    "japan": (36.2048, 138.2529),
    "Japan": (36.2048, 138.2529),

    # España / Spain
    "espana": (40.4637, -3.7492),
    "España": (40.4637, -3.7492),
    "spain": (40.4637, -3.7492),
    "Spain": (40.4637, -3.7492),

    # Francia / France
    "francia": (46.6034, 1.8883),
    "Francia": (46.6034, 1.8883),
    "france": (46.6034, 1.8883),
    "France": (46.6034, 1.8883),

    # Corea del Sur / South Korea
    "corea del sur": (35.9078, 127.7669),
    "Corea del Sur": (35.9078, 127.7669),
    "south korea": (35.9078, 127.7669),
    "South Korea": (35.9078, 127.7669),

    # México / Mexico
    "mexico": (23.6345, -102.5528),
    "México": (23.6345, -102.5528),
    "Mexico": (23.6345, -102.5528),
    "MEXICO": (23.6345, -102.5528),

    # Estados Unidos / EE.UU. / USA
    "eeuu": (37.0902, -95.7129),
    "EE.UU.": (37.0902, -95.7129),
    "estados unidos": (37.0902, -95.7129),
    "Estados Unidos": (37.0902, -95.7129),
    "usa": (37.0902, -95.7129),
    "USA": (37.0902, -95.7129),
    "united states": (37.0902, -95.7129),
    "United States": (37.0902, -95.7129),

    # India
    "india": (20.5937, 78.9629),
    "India": (20.5937, 78.9629),

    # Sudáfrica / South Africa
    "sudafrica": (-30.5595, 22.9375),
    "Sudáfrica": (-30.5595, 22.9375),
    "south africa": (-30.5595, 22.9375),
    "South Africa": (-30.5595, 22.9375),

    # Perú / Peru
    "peru": (-9.19, -75.0152),
    "Peru": (-9.19, -75.0152),
    "perú": (-9.19, -75.0152),
    "Perú": (-9.19, -75.0152),

    # Chile
    "chile": (-35.6751, -71.5430),
    "Chile": (-35.6751, -71.5430),

    # Egipto / Egypt
    "egipto": (26.8206, 30.8025),
    "Egipto": (26.8206, 30.8025),
    "egypt": (26.8206, 30.8025),
    "Egypt": (26.8206, 30.8025),

    # Colombia
    "colombia": (4.5709, -74.2973),
    "Colombia": (4.5709, -74.2973),

    # Vietnam
    "vietnam": (14.0583, 108.2772),
    "Vietnam": (14.0583, 108.2772),

    # Argentina
    "argentina": (-38.4161, -63.6167),
    "Argentina": (-38.4161, -63.6167),
    # Argentina
    "argentina": (-38.4161, -63.6167),
    "Argentina": (-38.4161, -63.6167),
    "republica argentina": (-38.4161, -63.6167),
    "Republica Argentina": (-38.4161, -63.6167),
    "rep argentina": (-38.4161, -63.6167),
    "Rep Argentina": (-38.4161, -63.6167),

}




@router.get("/api/trade-flows")
def get_trade_flows():
    """
    Lee app/data/dataset.xlsx con columnas:
    origin, destination, product, quantity, unit_price, tariff, date, total_price

    Devuelve TODAS las filas del dataset.
    - Si se conocen coordenadas del país -> se incluyen.
    - Si no, origin_lat/origin_lng/destination_lat/destination_lng van como null.
    """
    if not DATASET_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="dataset.xlsx no encontrado en app/data/",
        )

    try:
        df = pd.read_excel(DATASET_PATH)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo leer dataset.xlsx: {e}",
        )

    required_cols = {
        "origin",
        "destination",
        "product",
        "quantity",
        "unit_price",
        "tariff",
        "date",
        "total_price",
    }
    if not required_cols.issubset(df.columns):
        raise HTTPException(
            status_code=400,
            detail=(
                "dataset.xlsx debe tener las columnas: "
                + ", ".join(sorted(required_cols))
            ),
        )

    flows = []

    def to_float(v, default=0.0):
        try:
            return float(v)
        except Exception:
            return default

    for _, row in df.iterrows():
        origin_raw = str(row["origin"])
        destination_raw = str(row["destination"])

        origin = origin_raw.strip()
        destination = destination_raw.strip()

        quantity = to_float(row["quantity"])
        unit_price = to_float(row["unit_price"])
        tariff = to_float(row["tariff"])
        total_price = to_float(row["total_price"], quantity * unit_price)

        # Normalizamos para buscar coordenadas
        origin_key = normalize_country(origin)
        dest_key = normalize_country(destination)

        origin_coords = COUNTRY_COORDS.get(origin_key)
        dest_coords = COUNTRY_COORDS.get(dest_key)

        flow = {
            "origin": origin,
            "destination": destination,
            "product": str(row["product"]),
            "quantity": quantity,
            "unit_price": unit_price,
            "tariff": tariff,
            "date": str(row["date"]),
            "total_price": total_price,
            "origin_lat": float(origin_coords[0]) if origin_coords else None,
            "origin_lng": float(origin_coords[1]) if origin_coords else None,
            "destination_lat": float(dest_coords[0]) if dest_coords else None,
            "destination_lng": float(dest_coords[1]) if dest_coords else None,
        }
        flows.append(flow)

    return {"flows": flows}

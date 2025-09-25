# data_loader.py
import pandas as pd
import networkx as nx

def build_graph_from_excel(path: str = "data/dataset.xlsx") -> nx.DiGraph:
    G = nx.DiGraph()
    try:
        df = pd.read_excel(path)

        # Columnas esperadas:
        # origin | destination | product | quantity | unit_price | total_price | tariff | [shipping_cost] | date
        for _, row in df.iterrows():
            origin = str(row["origin"]).strip()
            dest = str(row["destination"]).strip()
            product = str(row.get("product", "generic")).strip()

            tariff = float(row.get("tariff", 0) or 0)
            unit_price = float(row.get("unit_price", 0) or 0)

            # Si existe la columna shipping_cost, úsala; si no, valor = 0
            shipping = 0.0
            if "shipping_cost" in df.columns:
                shipping = float(row.get("shipping_cost", 0) or 0)

            # Fórmula del costo: tarifa % del unit_price + costo de envío
            cost = shipping + (tariff / 100.0) * unit_price

            if G.has_edge(origin, dest):
                existing = G[origin][dest].get("weight", float("inf"))
                if cost < existing:
                    G[origin][dest]["weight"] = cost
                    G[origin][dest]["product"] = product
            else:
                G.add_edge(
                    origin,
                    dest,
                    weight=cost,
                    product=product,
                    tariff=tariff,
                    shipping=shipping,
                )
    except FileNotFoundError:
        # fallback: datos simulados
        G.add_edge("Germany", "Portugal", weight=2.0, product="Paneles solares", tariff=2.0, shipping=1.0)
        G.add_edge("Portugal", "Brazil", weight=12.0, product="Paneles solares", tariff=10.0, shipping=2.0)
        G.add_edge("Germany", "Brazil", weight=20.0, product="Paneles solares", tariff=15.0, shipping=5.0)
    return G

GRAPH = build_graph_from_excel()

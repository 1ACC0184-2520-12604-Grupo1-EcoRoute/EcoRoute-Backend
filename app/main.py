from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import JSONResponse, Response
import traceback

from app.auth.routes import router as auth_router
from app.api.endpoints import router as rutas_router  # 👈 tu router actual (grafos, etc)
from app.api.trade_flows import router as trade_flows_router  # 👈 NUEVO
from app.reports import routes as reports_routes

app = FastAPI(title="EcoRoute API")

# SessionMiddleware para OAuth (Google)
app.add_middleware(
    SessionMiddleware,
    secret_key="CAMBIA_ESTE_SECRET_DE_SESION_POR_ALGO_UNICO_Y_LARGO",
    same_site="lax",
    https_only=False,
)

# CORS (incluye 5173 y 5174)
origins = [
    "https://ecoroute-frontend.web.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(rutas_router)         # 👈 aquí sigues teniendo TODO lo de /ruta-optima, Dijkstra, etc
app.include_router(trade_flows_router)   # 👈 endpoints para dataset.xlsx y mapa de flows


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/favicon.ico")
async def favicon():
    # evita error de favicon en consola
    return Response(status_code=204, media_type="image/x-icon")


# Handler global de errores (solo dev)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("🔥 Excepción no controlada:")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "path": request.url.path,
        },
    )


app.include_router(reports_routes.router)

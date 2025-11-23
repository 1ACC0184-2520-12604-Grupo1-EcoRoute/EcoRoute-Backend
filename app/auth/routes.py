import os
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from authlib.integrations.starlette_client import OAuth

from .schemas import UserCreate, UserLogin, UserOut, Token
from .service import user_service
from app.core.security import create_access_token, get_current_user
from app.database import get_db

router = APIRouter(tags=["Auth"])

# URL del frontend
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Credenciales Google
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

oauth = OAuth()
google_enabled = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

if google_enabled:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


@router.get("/login")
def login_info():
    return {"detail": "Usa POST /login desde el frontend para autenticarte."}


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = user_service.authenticate(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token = create_access_token(subject=user.username)
    return Token(access_token=access_token)


@router.post("/register", response_model=UserOut)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        return user_service.register_user(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=UserOut)
async def read_me(current_user: UserOut = Depends(get_current_user)):
    """
    Devuelve los datos del usuario autenticado a partir del JWT.
    (get_current_user debe ahora leer también desde la BD, lo ajustamos luego si quieres).
    """
    return current_user


@router.get("/auth/google/login")
async def google_login(request: Request):
    if not google_enabled:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth no está configurado en el servidor.",
        )
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    if not google_enabled:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth no está configurado en el servidor.",
        )

    token = await oauth.google.authorize_access_token(request)

    user_info = None

    if isinstance(token, dict):
        user_info = token.get("userinfo")

    if not user_info:
        try:
            resp = await oauth.google.get("userinfo", token=token)
            if resp.status_code == 200:
                user_info = resp.json()
        except Exception:
            pass

    if not user_info:
        raise HTTPException(
            status_code=400,
            detail="No se pudo obtener información del usuario desde Google.",
        )

    sub = user_info.get("sub")
    email = user_info.get("email")

    if not sub and not email:
        raise HTTPException(
            status_code=400,
            detail="Google no retornó identificador de usuario válido.",
        )

    username = f"google_{sub or email}"
    email = email or f"{username}@google.local"

    user = user_service.create_or_get_oauth_user(db, username=username, email=email)
    access_token = create_access_token(subject=user.username)

    redirect_url = (
        f"{FRONTEND_URL}/oauth-success"
        f"?token={access_token}&username={user.username}"
    )

    print("Google OAuth OK, redirigiendo a:", redirect_url)

    return RedirectResponse(url=redirect_url)

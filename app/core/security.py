from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import os

from app.database import get_db

# === Configuración JWT ===

SECRET_KEY = os.getenv(
    "ECO_ROUTE_SECRET",
    "CAMBIA_ESTE_VALOR_POR_UN_SECRET_LARGO_Y_UNICO_PARA_DESARROLLO",
)
ALGORITHM = os.getenv("ECO_ROUTE_ALGO", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ECO_ROUTE_TOKEN_MIN", "60"))

# Hash seguro
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": subject, "exp": expire}

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Obtiene el usuario autenticado desde un JWT.
    Ahora correctamente usa la BD y evita importaciones circulares.
    """

    # Importamos aquí para evitar el "circular import"
    from app.auth.service import user_service
    from app.auth.schemas import UserOut

    cred_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise cred_exception
    except JWTError:
        raise cred_exception

    # Obtener usuario REAL desde MySQL
    user = user_service.get_by_username(db, username)
    if user:
        return user

    # Token válido pero usuario no encontrado → usuario virtual
    return UserOut(
        id=0,
        username=username,
        email=f"{username}@virtual.local"
    )

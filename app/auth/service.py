import json
import os
import threading
from typing import Dict, Optional

from .schemas import UserCreate, UserOut
from app.core.security import get_password_hash, verify_password


class UserService:
    """
    Servicio de usuarios con persistencia sencilla en disco (users.json).
    Ideal para desarrollo: evita que los usuarios se pierdan al reiniciar el servidor.
    No es producción, pero es mucho mejor que solo memoria.
    """

    def __init__(self, path: str = "app/data/users.json") -> None:
        self._path = path
        self._lock = threading.Lock()
        self._users: Dict[str, Dict] = {}
        self._id_counter: int = 1
        self._load()

    # ==========================
    # Persistencia interna
    # ==========================

    def _load(self) -> None:
        """
        Carga usuarios desde el JSON si existe.
        """
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._users = data.get("users", {})
                self._id_counter = data.get("id_counter", 1)
            except Exception:
                # Si falla la lectura, arrancamos limpio para no romper el server.
                self._users = {}
                self._id_counter = 1

    def _save(self) -> None:
        """
        Guarda usuarios en el JSON.
        """
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        data = {
            "users": self._users,
            "id_counter": self._id_counter,
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ==========================
    # Registro clásico
    # ==========================

    def register_user(self, data: UserCreate) -> UserOut:
        with self._lock:
            if data.username in self._users:
                raise ValueError("El nombre de usuario ya está registrado.")

            if any(u["email"] == data.email for u in self._users.values()):
                raise ValueError("El correo ya está registrado.")

            hashed_pw = get_password_hash(data.password)

            user_dict = {
                "id": self._id_counter,
                "username": data.username,
                "email": data.email,
                "hashed_password": hashed_pw,
            }

            self._users[data.username] = user_dict
            self._id_counter += 1
            self._save()

            return UserOut(
                id=user_dict["id"],
                username=user_dict["username"],
                email=user_dict["email"],
            )

    # ==========================
    # Login clásico
    # ==========================

    def authenticate(self, username: str, password: str) -> Optional[UserOut]:
        user = self._users.get(username)
        if not user:
            return None

        if not verify_password(password, user["hashed_password"]):
            return None

        return UserOut(
            id=user["id"],
            username=user["username"],
            email=user["email"],
        )

    # ==========================
    # Utilidades
    # ==========================

    def get_by_username(self, username: str) -> Optional[UserOut]:
        user = self._users.get(username)
        if not user:
            return None

        return UserOut(
            id=user["id"],
            username=user["username"],
            email=user["email"],
        )

    # ==========================
    # Usuarios OAuth (Google)
    # ==========================

    def create_or_get_oauth_user(self, username: str, email: str) -> UserOut:
        """
        Si ya existe, lo devuelve.
        Si no, lo crea con una contraseña dummy (no usada para login manual).
        """
        with self._lock:
            existing = self._users.get(username)
            if existing:
                return UserOut(
                    id=existing["id"],
                    username=existing["username"],
                    email=existing["email"],
                )

            dummy_password = "oauth_dummy_pw"
            hashed_pw = get_password_hash(dummy_password)

            user_dict = {
                "id": self._id_counter,
                "username": username,
                "email": email,
                "hashed_password": hashed_pw,
            }

            self._users[username] = user_dict
            self._id_counter += 1
            self._save()

            return UserOut(
                id=user_dict["id"],
                username=user_dict["username"],
                email=user_dict["email"],
            )


user_service = UserService()

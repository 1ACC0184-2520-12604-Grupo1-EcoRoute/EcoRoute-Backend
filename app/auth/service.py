from typing import Optional

from sqlalchemy.orm import Session

from app.auth.schemas import UserCreate, UserOut
from app.core.security import get_password_hash, verify_password
from app.models.users import User


class UserService:
    """
    Servicio de usuarios usando la tabla 'users' en MySQL.
    """

    # Registro clásico
    def register_user(self, db: Session, data: UserCreate) -> UserOut:
        # ¿usuario ya existe?
        existing = db.query(User).filter(User.username == data.username).first()
        if existing:
            raise ValueError("El nombre de usuario ya está registrado.")

        # ¿correo ya existe?
        existing_email = db.query(User).filter(User.email == data.email).first()
        if existing_email:
            raise ValueError("El correo ya está registrado.")

        hashed_pw = get_password_hash(data.password)

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hashed_pw,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return UserOut(id=user.id, username=user.username, email=user.email)

    # Login clásico
    def authenticate(self, db: Session, username: str, password: str) -> Optional[UserOut]:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return UserOut(id=user.id, username=user.username, email=user.email)

    # Obtener por username (útil para get_current_user)
    def get_by_username(self, db: Session, username: str) -> Optional[UserOut]:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        return UserOut(id=user.id, username=user.username, email=user.email)

    # Usuarios OAuth (Google)
    def create_or_get_oauth_user(self, db: Session, username: str, email: str) -> UserOut:
        """
        Si ya existe, lo devuelve.
        Si no, lo crea con una contraseña dummy (no usada para login manual).
        """
        user = db.query(User).filter(User.username == username).first()
        if user:
            return UserOut(id=user.id, username=user.username, email=user.email)

        dummy_password = "oauth_dummy_pw"
        hashed_pw = get_password_hash(dummy_password)

        user = User(
            username=username,
            email=email,
            hashed_password=hashed_pw,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return UserOut(id=user.id, username=user.username, email=user.email)


user_service = UserService()

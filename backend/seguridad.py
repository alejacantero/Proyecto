import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database import usuarios  # también carga el .env

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

if not JWT_SECRET:
    raise ValueError("No se encontró JWT_SECRET en el archivo .env")

esquema_bearer = HTTPBearer()


def encriptar_password(password: str) -> str:
    hash_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except ValueError:
        return False


def crear_token(usuario_id: str, email: str, nombre: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": usuario_id,
        "email": email,
        "nombre": nombre,
        "exp": expira,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(esquema_bearer),
):
    try:
        payload = jwt.decode(
            credenciales.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El token ha expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario_id = payload.get("sub")

    if not usuario_id or not ObjectId.is_valid(usuario_id):
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = usuarios.find_one({"_id": ObjectId(usuario_id)})

    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return usuario

def requerir_admin(usuario: dict = Depends(obtener_usuario_actual)):
    if usuario.get("rol") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Se requiere rol de administrador"
        )
    return usuario
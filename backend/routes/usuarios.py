from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from database import usuarios
from schemas.usuario import UsuarioCrear, UsuarioLogin, UsuarioActualizar
from seguridad import (
    encriptar_password,
    verificar_password,
    crear_token,
    obtener_usuario_actual,
    requerir_admin,
)

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def limpiar_usuario(usuario: dict) -> dict:
    usuario["id"] = str(usuario["_id"])
    del usuario["_id"]
    usuario.pop("password", None)
    usuario.setdefault("rol", "cliente")
    return usuario


@router.post("/registro", status_code=201)
def registrar_usuario(usuario: UsuarioCrear):

    email = usuario.email.lower()

    if usuarios.find_one({"email": email}) is not None:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un usuario con ese correo"
        )

    nuevo = {
        "nombre": usuario.nombre,
        "email": email,
        "password": encriptar_password(usuario.password),
        "rol": "cliente",
    }

    resultado = usuarios.insert_one(nuevo)

    return {
        "mensaje": "Usuario creado correctamente",
        "id": str(resultado.inserted_id)
    }


@router.post("/login")
def login(datos: UsuarioLogin):

    usuario = usuarios.find_one({"email": datos.email.lower()})

    if usuario is None or not verificar_password(
        datos.password, usuario.get("password", "")
    ):
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos"
        )

    token = crear_token(
        usuario_id=str(usuario["_id"]),
        email=usuario["email"],
        nombre=usuario["nombre"],
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": limpiar_usuario(usuario),
    }


@router.get("/me")
def perfil_actual(usuario: dict = Depends(obtener_usuario_actual)):
    return limpiar_usuario(usuario)


@router.get("/")
def listar_usuarios(admin: dict = Depends(requerir_admin)):
    return [limpiar_usuario(u) for u in usuarios.find()]


@router.get("/{usuario_id}")
def obtener_usuario(usuario_id: str, admin: dict = Depends(requerir_admin)):

    if not ObjectId.is_valid(usuario_id):
        raise HTTPException(status_code=400, detail="ID de usuario inválido")

    usuario = usuarios.find_one({"_id": ObjectId(usuario_id)})

    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return limpiar_usuario(usuario)


@router.put("/{usuario_id}")
def actualizar_usuario(
    usuario_id: str,
    datos: UsuarioActualizar,
    admin: dict = Depends(requerir_admin),
):

    if not ObjectId.is_valid(usuario_id):
        raise HTTPException(status_code=400, detail="ID de usuario inválido")

    if str(admin["_id"]) == usuario_id and datos.rol != "admin":
        raise HTTPException(
            status_code=400,
            detail="No puedes quitarte el rol de administrador a ti mismo"
        )

    resultado = usuarios.update_one(
        {"_id": ObjectId(usuario_id)},
        {"$set": {"nombre": datos.nombre, "rol": datos.rol}}
    )

    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"mensaje": "Usuario actualizado correctamente"}


@router.delete("/{usuario_id}")
def eliminar_usuario(usuario_id: str, admin: dict = Depends(requerir_admin)):

    if not ObjectId.is_valid(usuario_id):
        raise HTTPException(status_code=400, detail="ID de usuario inválido")

    if str(admin["_id"]) == usuario_id:
        raise HTTPException(
            status_code=400,
            detail="No puedes eliminar tu propia cuenta"
        )

    resultado = usuarios.delete_one({"_id": ObjectId(usuario_id)})

    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"mensaje": "Usuario eliminado correctamente"}
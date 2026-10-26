
from fastapi import APIRouter, HTTPException
from bson import ObjectId

from database import usuarios
from schemas.usuario import UsuarioCrear

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.post("/")
def crear_usuario(usuario: UsuarioCrear):

    datos = usuario.model_dump()

    usuario_existente = usuarios.find_one({
        "email": datos["email"]
    })

    if usuario_existente is not None:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un usuario con ese correo"
        )

    resultado = usuarios.insert_one(datos)

    return {
        "mensaje": "Usuario creado correctamente",
        "id": str(resultado.inserted_id)
    }


@router.get("/")
def listar_usuarios():

    lista = []

    for usuario in usuarios.find():
        usuario["id"] = str(usuario["_id"])
        del usuario["_id"]

        lista.append(usuario)

    return lista


@router.get("/{usuario_id}")
def obtener_usuario(usuario_id: str):

    if not ObjectId.is_valid(usuario_id):
        raise HTTPException(
            status_code=400,
            detail="ID de usuario inválido"
        )

    usuario = usuarios.find_one({
        "_id": ObjectId(usuario_id)
    })

    if usuario is None:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    usuario["id"] = str(usuario["_id"])
    del usuario["_id"]

    return usuario

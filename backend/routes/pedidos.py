from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime, timezone

from database import pedidos, productos, usuarios
from schemas.pedido import PedidoCrear, PedidoEstado
from seguridad import obtener_usuario_actual, requerir_admin

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


def limpiar_pedido(pedido: dict) -> dict:
    pedido["id"] = str(pedido["_id"])
    pedido["usuario_id"] = str(pedido["usuario_id"])
    pedido["producto_id"] = str(pedido["producto_id"])
    pedido["fecha"] = pedido["fecha"].isoformat()
    del pedido["_id"]
    return pedido


@router.post("/", status_code=201)
def crear_pedido(
    pedido: PedidoCrear,
    actual: dict = Depends(obtener_usuario_actual),
):

    if not ObjectId.is_valid(pedido.usuario_id):
        raise HTTPException(status_code=400, detail="ID de usuario inválido")

    if not ObjectId.is_valid(pedido.producto_id):
        raise HTTPException(status_code=400, detail="ID de producto inválido")

    usuario = usuarios.find_one({"_id": ObjectId(pedido.usuario_id)})

    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    producto = productos.find_one({"_id": ObjectId(pedido.producto_id)})

    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    resultado = productos.update_one(
        {
            "_id": ObjectId(pedido.producto_id),
            "stock": {"$gte": pedido.cantidad}
        },
        {"$inc": {"stock": -pedido.cantidad}}
    )

    if resultado.modified_count == 0:
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    datos = pedido.model_dump()
    datos["usuario_id"] = ObjectId(pedido.usuario_id)
    datos["producto_id"] = ObjectId(pedido.producto_id)
    datos["estado"] = "registrado"
    datos["fecha"] = datetime.now(timezone.utc)

    resultado = pedidos.insert_one(datos)

    return {
        "mensaje": "Pedido registrado correctamente",
        "id": str(resultado.inserted_id)
    }


@router.get("/")
def listar_pedidos(admin: dict = Depends(requerir_admin)):
    return [limpiar_pedido(p) for p in pedidos.find()]


@router.get("/{pedido_id}")
def obtener_pedido(pedido_id: str, admin: dict = Depends(requerir_admin)):

    if not ObjectId.is_valid(pedido_id):
        raise HTTPException(status_code=400, detail="ID de pedido inválido")

    pedido = pedidos.find_one({"_id": ObjectId(pedido_id)})

    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    return limpiar_pedido(pedido)


@router.put("/{pedido_id}")
def actualizar_estado(
    pedido_id: str,
    datos: PedidoEstado,
    admin: dict = Depends(requerir_admin),
):

    if not ObjectId.is_valid(pedido_id):
        raise HTTPException(status_code=400, detail="ID de pedido inválido")

    pedido = pedidos.find_one({"_id": ObjectId(pedido_id)})

    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    if pedido["estado"] == "cancelado":
        raise HTTPException(
            status_code=400,
            detail="Un pedido cancelado no se puede modificar"
        )

    if datos.estado == "cancelado":
        productos.update_one(
            {"_id": pedido["producto_id"]},
            {"$inc": {"stock": pedido["cantidad"]}}
        )

    pedidos.update_one(
        {"_id": ObjectId(pedido_id)},
        {"$set": {"estado": datos.estado}}
    )

    return {"mensaje": "Estado del pedido actualizado"}


@router.delete("/{pedido_id}")
def eliminar_pedido(pedido_id: str, admin: dict = Depends(requerir_admin)):

    if not ObjectId.is_valid(pedido_id):
        raise HTTPException(status_code=400, detail="ID de pedido inválido")

    pedido = pedidos.find_one({"_id": ObjectId(pedido_id)})

    if pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    if pedido["estado"] != "cancelado":
        productos.update_one(
            {"_id": pedido["producto_id"]},
            {"$inc": {"stock": pedido["cantidad"]}}
        )

    pedidos.delete_one({"_id": ObjectId(pedido_id)})

    return {"mensaje": "Pedido eliminado correctamente"}
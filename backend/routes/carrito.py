from pymongo.errors import PyMongoError
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from database import carritos, pedidos, productos
from schemas.carrito import CantidadItem, ItemCarrito
from seguridad import obtener_usuario_actual

router = APIRouter(prefix="/carrito", tags=["Carrito"])


def ahora():
    return datetime.now(timezone.utc)


def armar_carrito(usuario: dict) -> dict:
    """Devuelve el carrito del usuario con los datos actuales de cada producto."""
    carrito = carritos.find_one({"usuario_id": usuario["_id"]}) or {}
    items = []
    huerfanos = []
    total = 0
    cantidad_total = 0

    for it in carrito.get("items", []):
        producto = productos.find_one({"_id": it["producto_id"]})

        if producto is None:  # el admin eliminó el producto
            huerfanos.append(it["producto_id"])
            continue

        subtotal = producto["precio"] * it["cantidad"]
        total += subtotal
        cantidad_total += it["cantidad"]

        items.append({
            "producto_id": str(producto["_id"]),
            "nombre": producto["nombre"],
            "categoria": producto["categoria"],
            "precio": producto["precio"],
            "cantidad": it["cantidad"],
            "stock": producto["stock"],
            "subtotal": round(subtotal, 2),
            "sin_stock": it["cantidad"] > producto["stock"],
        })

    if huerfanos:
        carritos.update_one(
            {"usuario_id": usuario["_id"]},
            {"$pull": {"items": {"producto_id": {"$in": huerfanos}}}}
        )

    return {
        "items": items,
        "total": round(total, 2),
        "cantidad_total": cantidad_total,
    }


def respuesta(usuario: dict, mensaje: str) -> dict:
    carrito = armar_carrito(usuario)
    carrito["mensaje"] = mensaje
    return carrito


def buscar_producto(producto_id: str) -> dict:
    if not ObjectId.is_valid(producto_id):
        raise HTTPException(status_code=400, detail="ID de producto inválido")

    producto = productos.find_one({"_id": ObjectId(producto_id)})

    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return producto


@router.get("/")
def ver_carrito(usuario: dict = Depends(obtener_usuario_actual)):
    return armar_carrito(usuario)


@router.post("/items", status_code=201)
def agregar_item(item: ItemCarrito, usuario: dict = Depends(obtener_usuario_actual)):
    producto = buscar_producto(item.producto_id)
    pid = producto["_id"]

    carrito = carritos.find_one({"usuario_id": usuario["_id"]}) or {}
    actual = 0

    for it in carrito.get("items", []):
        if it["producto_id"] == pid:
            actual = it["cantidad"]

    nueva = actual + item.cantidad

    if nueva > producto["stock"]:
        raise HTTPException(
            status_code=400,
            detail=f"Solo hay {producto['stock']} unidades disponibles de {producto['nombre']}"
        )

    if actual:
        carritos.update_one(
            {"usuario_id": usuario["_id"], "items.producto_id": pid},
            {"$set": {"items.$.cantidad": nueva, "actualizado": ahora()}}
        )
    else:
        carritos.update_one(
            {"usuario_id": usuario["_id"]},
            {
                "$push": {"items": {"producto_id": pid, "cantidad": item.cantidad}},
                "$set": {"actualizado": ahora()},
            },
            upsert=True
        )

    return respuesta(usuario, "Producto añadido al carrito")


@router.put("/items/{producto_id}")
def cambiar_cantidad(
    producto_id: str,
    datos: CantidadItem,
    usuario: dict = Depends(obtener_usuario_actual),
):
    producto = buscar_producto(producto_id)

    if datos.cantidad > producto["stock"]:
        raise HTTPException(
            status_code=400,
            detail=f"Solo hay {producto['stock']} unidades disponibles de {producto['nombre']}"
        )

    resultado = carritos.update_one(
        {"usuario_id": usuario["_id"], "items.producto_id": producto["_id"]},
        {"$set": {"items.$.cantidad": datos.cantidad, "actualizado": ahora()}}
    )

    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ese producto no está en tu carrito")

    return respuesta(usuario, "Cantidad actualizada")


@router.delete("/items/{producto_id}")
def quitar_item(producto_id: str, usuario: dict = Depends(obtener_usuario_actual)):
    if not ObjectId.is_valid(producto_id):
        raise HTTPException(status_code=400, detail="ID de producto inválido")

    resultado = carritos.update_one(
        {"usuario_id": usuario["_id"]},
        {
            "$pull": {"items": {"producto_id": ObjectId(producto_id)}},
            "$set": {"actualizado": ahora()},
        }
    )

    if resultado.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ese producto no está en tu carrito")

    return respuesta(usuario, "Producto eliminado del carrito")


@router.delete("/")
def vaciar_carrito(usuario: dict = Depends(obtener_usuario_actual)):
    carritos.delete_one({"usuario_id": usuario["_id"]})
    return respuesta(usuario, "Carrito vaciado")


@router.post("/confirmar", status_code=201)
def devolver_stock(descontados: list):
    for it in descontados:
        try:
            productos.update_one(
                {"_id": it["producto_id"]},
                {"$inc": {"stock": it["cantidad"]}}
            )
        except PyMongoError:
            pass  # si Mongo está caído no hay nada más que hacer


@router.post("/confirmar", status_code=201)
def confirmar_pedido(usuario: dict = Depends(obtener_usuario_actual)):
    carrito = carritos.find_one({"usuario_id": usuario["_id"]})

    if carrito is None or not carrito.get("items"):
        raise HTTPException(status_code=400, detail="Tu carrito está vacío")

    compra_id = str(ObjectId())
    fecha = ahora()
    descontados = []
    nuevos = []
    total = 0

    try:
        for it in carrito["items"]:
            producto = productos.find_one({"_id": it["producto_id"]})

            if producto is None:
                raise HTTPException(
                    status_code=400,
                    detail="Un producto de tu carrito ya no existe. Quítalo e intenta de nuevo"
                )

            # Descuento atómico: solo si todavía hay stock suficiente
            resultado = productos.update_one(
                {"_id": it["producto_id"], "stock": {"$gte": it["cantidad"]}},
                {"$inc": {"stock": -it["cantidad"]}}
            )

            if resultado.modified_count == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente para {producto['nombre']}"
                )

            descontados.append(it)
            total += producto["precio"] * it["cantidad"]

            nuevos.append({
                "usuario_id": usuario["_id"],
                "producto_id": it["producto_id"],
                "cantidad": it["cantidad"],
                "precio_unitario": producto["precio"],
                "estado": "registrado",
                "fecha": fecha,
                "compra_id": compra_id,
            })

        pedidos.insert_many(nuevos)

    except Exception:
        devolver_stock(descontados)
        raise

    carritos.delete_one({"usuario_id": usuario["_id"]})

    return {
        "mensaje": "Pedido confirmado correctamente",
        "compra_id": compra_id,
        "articulos": len(nuevos),
        "total": round(total, 2),
        "cantidad_total": 0,
    }
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from database import productos
from schemas.producto import ProductoCrear
from seguridad import requerir_admin

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.post("/", status_code=201)
def crear_producto(producto: ProductoCrear, admin: dict = Depends(requerir_admin)):
    resultado = productos.insert_one(producto.model_dump())

    return {
        "mensaje": "Producto creado correctamente",
        "id": str(resultado.inserted_id)
    }


@router.get("/")
def listar_productos():
    lista = []

    for producto in productos.find():
        producto["id"] = str(producto["_id"])
        del producto["_id"]
        lista.append(producto)

    return lista


@router.get("/{producto_id}")
def obtener_producto(producto_id: str):
    if not ObjectId.is_valid(producto_id):
        raise HTTPException(status_code=400, detail="ID inválido")

    producto = productos.find_one({"_id": ObjectId(producto_id)})

    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    producto["id"] = str(producto["_id"])
    del producto["_id"]

    return producto


@router.put("/{producto_id}")
def actualizar_producto(
    producto_id: str,
    producto: ProductoCrear,
    admin: dict = Depends(requerir_admin),
):
    if not ObjectId.is_valid(producto_id):
        raise HTTPException(status_code=400, detail="ID inválido")

    resultado = productos.update_one(
        {"_id": ObjectId(producto_id)},
        {"$set": producto.model_dump()}
    )

    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return {"mensaje": "Producto actualizado correctamente"}


@router.delete("/{producto_id}")
def eliminar_producto(producto_id: str, admin: dict = Depends(requerir_admin)):
    if not ObjectId.is_valid(producto_id):
        raise HTTPException(status_code=400, detail="ID inválido")

    resultado = productos.delete_one({"_id": ObjectId(producto_id)})

    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return {"mensaje": "Producto eliminado correctamente"}
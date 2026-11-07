import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

from routes.productos import router as productos_router
from routes.pedidos import router as pedidos_router
from routes.usuarios import router as usuarios_router
from routes.carrito import router as carrito_router

logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="TechGear API",
    description="API para gestionar productos, pedidos, usuarios y carrito",
    version="1.0.0"
)

app.include_router(productos_router)
app.include_router(pedidos_router)
app.include_router(usuarios_router)
app.include_router(carrito_router)


@app.exception_handler(PyMongoError)
async def error_base_de_datos(request: Request, exc: PyMongoError):
    logger.error("Error de MongoDB: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "La base de datos no está disponible. Intenta de nuevo en unos minutos."},
    )


@app.exception_handler(Exception)
async def error_inesperado(request: Request, exc: Exception):
    logger.exception("Error inesperado: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


@app.get("/")
def inicio():
    return {"mensaje": "TechGear API funcionando"}
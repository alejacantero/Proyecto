
from fastapi import FastAPI

from routes.productos import router as productos_router
from routes.pedidos import router as pedidos_router
from routes.usuarios import router as usuarios_router

app = FastAPI(
    title="TechGear API",
    description="API para gestionar productos, pedidos y usuarios",
    version="1.0.0"
)

app.include_router(productos_router)
app.include_router(pedidos_router)
app.include_router(usuarios_router)


@app.get("/")
def inicio():
    return {"mensaje": "TechGear API funcionando"}

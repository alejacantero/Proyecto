
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

RUTA_ENV = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(RUTA_ENV)

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "tienda")

if not MONGO_URI:
    raise ValueError("No se encontró MONGO_URI en el archivo .env")

cliente = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

cliente.admin.command("ping")

db = cliente[DATABASE_NAME]

productos = db["productos"]
pedidos = db["pedidos"]
usuarios = db["usuarios"]

print("Conexión a MongoDB exitosa")
print("Base de datos utilizada:", DATABASE_NAME)
print("Colección de productos:", productos.name)
print("Colección de usuarios:", usuarios.name)

import sys
from database import usuarios

if len(sys.argv) != 2:
    print("Uso: python hacer_admin.py correo@ejemplo.com")
    sys.exit(1)

resultado = usuarios.update_one(
    {"email": sys.argv[1].lower()},
    {"$set": {"rol": "admin"}}
)

print("Listo, ahora es admin." if resultado.matched_count else "No existe ese usuario.")
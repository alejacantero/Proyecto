
from database import cliente, db

try:
    cliente.admin.command("ping")
    print("Conexión exitosa con MongoDB Atlas")
    print("Base de datos:", db.name)

except Exception as error:
    print("Error de conexión:", error)

finally:
    cliente.close()


import requests
from django.shortcuts import render

API_URL = "http://127.0.0.1:8000"

def listar_productos(request):
    productos = []
    error = None

    try:
        respuesta = requests.get(f"{API_URL}/productos/", timeout=10)
        respuesta.raise_for_status()
        productos = respuesta.json()

    except requests.exceptions.ConnectionError:
        error = "No se pudo establecer conexión con FastAPI."

    except requests.exceptions.Timeout:
        error = "La API tardó demasiado en responder."

    except requests.exceptions.RequestException as e:
        error = f"Error al consultar la API: {e}"

    return render(
        request,
        "tienda/productos.html",
        {
            "productos": productos,
            "error": error
        }
    )

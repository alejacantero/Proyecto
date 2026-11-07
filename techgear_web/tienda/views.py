import requests
from .views_admin import detalle_error
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect

API_URL = settings.API_URL


def listar_productos(request):
    productos = []
    error = None

    try:
        respuesta = requests.get(f"{API_URL}/productos/", timeout=30)

        if respuesta.ok:
            productos = respuesta.json()
        else:
            error = detalle_error(respuesta)

    except requests.exceptions.Timeout:
        error = "La API tardó demasiado en responder. Intenta de nuevo en unos segundos."

    except requests.exceptions.ConnectionError:
        error = "No se pudo establecer conexión con FastAPI."

    except requests.exceptions.RequestException:
        error = "La API devolvió una respuesta inesperada."

    categorias = sorted({p.get("categoria", "") for p in productos if p.get("categoria")})
    busqueda = request.GET.get("q", "").strip()
    categoria_sel = request.GET.get("categoria", "")

    if categoria_sel:
        productos = [p for p in productos if p.get("categoria") == categoria_sel]

    if busqueda:
        texto = busqueda.lower()
        productos = [
            p for p in productos
            if texto in p.get("nombre", "").lower()
            or texto in p.get("descripcion", "").lower()
        ]

    return render(
        request,
        "tienda/productos.html",
        {
            "productos": productos,
            "error": error,
            "categorias": categorias,
            "busqueda": busqueda,
            "categoria_sel": categoria_sel,
        },
    )

def iniciar_sesion(request):
    if request.session.get("token"):
        return redirect("catalogo")

    contexto = {"error": None, "email": ""}

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        contexto["email"] = email

        try:
            respuesta = requests.post(
                f"{API_URL}/usuarios/login",
                json={"email": email, "password": password},
                timeout=30,
            )

            if respuesta.status_code == 200:
                datos = respuesta.json()
                request.session["token"] = datos["access_token"]
                request.session["usuario"] = {
                    "nombre": datos["usuario"]["nombre"],
                    "email": datos["usuario"]["email"],
                    "rol": datos["usuario"].get("rol", "cliente"),
                }

                # Cargar cuántos artículos tiene ya en su carrito guardado
                try:
                    carrito = requests.get(
                        f"{API_URL}/carrito/",
                        headers={"Authorization": f"Bearer {datos['access_token']}"},
                        timeout=30,
                    )
                    request.session["carrito_n"] = (
                        carrito.json().get("cantidad_total", 0) if carrito.ok else 0
                    )
                except (requests.exceptions.RequestException, ValueError):
                    request.session["carrito_n"] = 0

                messages.success(request, "Sesión iniciada correctamente.")
                return redirect("catalogo")

            elif respuesta.status_code == 401:
                contexto["error"] = "Correo o contraseña incorrectos."
            else:
                contexto["error"] = "Revisa que el correo y la contraseña sean válidos."

        except requests.exceptions.RequestException:
            contexto["error"] = "No se pudo conectar con la API."

    return render(request, "tienda/login.html", contexto)


def registro(request):
    if request.session.get("token"):
        return redirect("catalogo")

    contexto = {"error": None, "nombre": "", "email": ""}

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        contexto["nombre"] = nombre
        contexto["email"] = email

        if password != password2:
            contexto["error"] = "Las contraseñas no coinciden."
            return render(request, "tienda/registro.html", contexto)

        try:
            respuesta = requests.post(
                f"{API_URL}/usuarios/registro",
                json={"nombre": nombre, "email": email, "password": password},
                timeout=30,
            )

            if respuesta.status_code == 201:
                messages.success(request, "Cuenta creada. Ahora inicia sesión.")
                return redirect("login")

            elif respuesta.status_code == 400:
                contexto["error"] = respuesta.json().get("detail", "No se pudo registrar.")
            else:
                contexto["error"] = "Datos inválidos: revisa el correo y que la contraseña tenga entre 6 y 72 caracteres."

        except requests.exceptions.RequestException:
            contexto["error"] = "No se pudo conectar con la API."

    return render(request, "tienda/registro.html", contexto)


def cerrar_sesion(request):
    request.session.flush()
    messages.info(request, "Sesión cerrada.")
    return redirect("catalogo")
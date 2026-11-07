from datetime import datetime
from functools import wraps

import requests
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

API_URL = settings.API_URL
ESTADOS = ["registrado", "enviado", "entregado", "cancelado"]


class SesionExpirada(Exception):
    pass


def admin_requerido(vista):
    """Solo deja pasar a usuarios con sesión y rol admin."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        usuario = request.session.get("usuario")

        if not request.session.get("token") or not usuario:
            messages.warning(request, "Inicia sesión para entrar al panel.")
            return redirect("login")

        if usuario.get("rol") != "admin":
            messages.error(request, "No tienes permisos de administrador.")
            return redirect("catalogo")

        try:
            return vista(request, *args, **kwargs)
        except SesionExpirada:
            request.session.flush()
            messages.warning(request, "Tu sesión expiró. Inicia sesión de nuevo.")
            return redirect("login")
        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con la API.")
            return redirect("catalogo")

    return envoltura


def api(request, metodo, ruta, datos=None):
    """Llama a FastAPI enviando el JWT guardado en la sesión."""
    respuesta = requests.request(
        metodo,
        f"{API_URL}{ruta}",
        json=datos,
        headers={"Authorization": f"Bearer {request.session.get('token')}"},
        timeout=30,
    )
    if respuesta.status_code == 401:
        raise SesionExpirada()
    return respuesta


def detalle_error(respuesta):
    try:
        detalle = respuesta.json().get("detail")
    except (ValueError, AttributeError):
        detalle = None

    if isinstance(detalle, list):  # errores de validación de Pydantic
        return "; ".join(f"{e['loc'][-1]}: {e['msg']}" for e in detalle)

    if detalle:
        return detalle

    if respuesta.status_code in (502, 503, 504):
        return "La API no está disponible en este momento (puede estar iniciando). Intenta en unos segundos."

    return f"Error {respuesta.status_code} de la API"


def obtener_lista(request, ruta):
    respuesta = api(request, "GET", ruta)
    if not respuesta.ok:
        messages.error(request, detalle_error(respuesta))
        return []
    return respuesta.json()


# ---------- Inicio ----------

@admin_requerido
def admin_inicio(request):
    return redirect("admin_productos")


# ---------- Productos ----------

@admin_requerido
def admin_productos(request):
    return render(request, "tienda/admin_productos.html", {
        "productos": obtener_lista(request, "/productos/"),
        "seccion": "productos",
    })


@admin_requerido
def admin_producto_form(request, producto_id=None):
    producto = {}

    if producto_id:
        respuesta = api(request, "GET", f"/productos/{producto_id}")
        if not respuesta.ok:
            messages.error(request, detalle_error(respuesta))
            return redirect("admin_productos")
        producto = respuesta.json()

    if request.method == "POST":
        try:
            datos = {
                "nombre": request.POST.get("nombre", "").strip(),
                "descripcion": request.POST.get("descripcion", "").strip(),
                "precio": float(request.POST.get("precio") or 0),
                "stock": int(request.POST.get("stock") or 0),
                "categoria": request.POST.get("categoria", "").strip(),
            }
        except ValueError:
            messages.error(request, "El precio y el stock deben ser números válidos.")
            return render(request, "tienda/admin_producto_form.html", {
                "producto": request.POST, "seccion": "productos",
            })

        if producto_id:
            respuesta = api(request, "PUT", f"/productos/{producto_id}", datos)
        else:
            respuesta = api(request, "POST", "/productos/", datos)

        if respuesta.ok:
            messages.success(request, "Producto guardado correctamente.")
            return redirect("admin_productos")

        messages.error(request, detalle_error(respuesta))
        producto = {**datos, "id": producto_id}

    return render(request, "tienda/admin_producto_form.html", {
        "producto": producto, "seccion": "productos",
    })


@admin_requerido
@require_POST
def admin_producto_eliminar(request, producto_id):
    respuesta = api(request, "DELETE", f"/productos/{producto_id}")
    if respuesta.ok:
        messages.success(request, "Producto eliminado.")
    else:
        messages.error(request, detalle_error(respuesta))
    return redirect("admin_productos")


# ---------- Usuarios ----------

@admin_requerido
def admin_usuarios(request):
    return render(request, "tienda/admin_usuarios.html", {
        "usuarios": obtener_lista(request, "/usuarios/"),
        "seccion": "usuarios",
    })


@admin_requerido
def admin_usuario_editar(request, usuario_id):
    respuesta = api(request, "GET", f"/usuarios/{usuario_id}")
    if not respuesta.ok:
        messages.error(request, detalle_error(respuesta))
        return redirect("admin_usuarios")

    usuario = respuesta.json()

    if request.method == "POST":
        datos = {
            "nombre": request.POST.get("nombre", "").strip(),
            "rol": request.POST.get("rol", "cliente"),
        }
        respuesta = api(request, "PUT", f"/usuarios/{usuario_id}", datos)

        if respuesta.ok:
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect("admin_usuarios")

        messages.error(request, detalle_error(respuesta))
        usuario.update(datos)

    return render(request, "tienda/admin_usuario_form.html", {
        "usuario": usuario, "seccion": "usuarios",
    })


@admin_requerido
@require_POST
def admin_usuario_eliminar(request, usuario_id):
    respuesta = api(request, "DELETE", f"/usuarios/{usuario_id}")
    if respuesta.ok:
        messages.success(request, "Usuario eliminado.")
    else:
        messages.error(request, detalle_error(respuesta))
    return redirect("admin_usuarios")


# ---------- Pedidos ----------

@admin_requerido
def admin_pedidos(request):
    lista = obtener_lista(request, "/pedidos/")
    usuarios = {u["id"]: u for u in obtener_lista(request, "/usuarios/")}
    productos = {p["id"]: p for p in obtener_lista(request, "/productos/")}

    for pedido in lista:
        pedido["usuario_nombre"] = usuarios.get(pedido["usuario_id"], {}).get("nombre", "(eliminado)")
        pedido["producto_nombre"] = productos.get(pedido["producto_id"], {}).get("nombre", "(eliminado)")
        try:
            pedido["fecha"] = datetime.fromisoformat(pedido["fecha"])
        except (ValueError, KeyError):
            pass

    lista.reverse()  # los más recientes primero

    return render(request, "tienda/admin_pedidos.html", {
        "pedidos": lista, "estados": ESTADOS, "seccion": "pedidos",
    })


@admin_requerido
def admin_pedido_crear(request):
    if request.method == "POST":
        try:
            cantidad = int(request.POST.get("cantidad", 0))
        except ValueError:
            cantidad = 0

        datos = {
            "usuario_id": request.POST.get("usuario_id", ""),
            "producto_id": request.POST.get("producto_id", ""),
            "cantidad": cantidad,
        }
        respuesta = api(request, "POST", "/pedidos/", datos)

        if respuesta.ok:
            messages.success(request, "Pedido creado y stock descontado.")
            return redirect("admin_pedidos")

        messages.error(request, detalle_error(respuesta))

    return render(request, "tienda/admin_pedido_form.html", {
        "usuarios": obtener_lista(request, "/usuarios/"),
        "productos": obtener_lista(request, "/productos/"),
        "seccion": "pedidos",
    })


@admin_requerido
@require_POST
def admin_pedido_estado(request, pedido_id):
    respuesta = api(request, "PUT", f"/pedidos/{pedido_id}",
                    {"estado": request.POST.get("estado", "")})
    if respuesta.ok:
        messages.success(request, "Estado actualizado.")
    else:
        messages.error(request, detalle_error(respuesta))
    return redirect("admin_pedidos")


@admin_requerido
@require_POST
def admin_pedido_eliminar(request, pedido_id):
    respuesta = api(request, "DELETE", f"/pedidos/{pedido_id}")
    if respuesta.ok:
        messages.success(request, "Pedido eliminado.")
    else:
        messages.error(request, detalle_error(respuesta))
    return redirect("admin_pedidos")
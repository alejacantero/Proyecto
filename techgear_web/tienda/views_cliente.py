from datetime import datetime
from functools import wraps

import requests
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .views_admin import SesionExpirada, api, detalle_error


def sesion_requerida(vista):
    """Solo deja pasar a usuarios con sesión iniciada."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.session.get("token"):
            messages.warning(request, "Inicia sesión para usar el carrito.")
            return redirect("login")

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


def destino(request, defecto):
    """Vuelve a la página de donde vino el usuario (solo rutas del mismo sitio)."""
    volver = request.POST.get("volver", "")

    if volver and url_has_allowed_host_and_scheme(volver, allowed_hosts={request.get_host()}):
        return redirect(volver)

    return redirect(defecto)


def operar(request, metodo, ruta, datos=None, exito=""):
    """Llama a la API, actualiza el contador del carrito y muestra el mensaje."""
    respuesta = api(request, metodo, ruta, datos)

    if respuesta.ok:
        request.session["carrito_n"] = respuesta.json().get("cantidad_total", 0)
        messages.success(request, exito)
    else:
        messages.error(request, detalle_error(respuesta))

    return respuesta


# ---------- Carrito ----------

@sesion_requerida
def carrito_ver(request):
    respuesta = api(request, "GET", "/carrito/")

    if respuesta.ok:
        carrito = respuesta.json()
        request.session["carrito_n"] = carrito["cantidad_total"]
    else:
        messages.error(request, detalle_error(respuesta))
        carrito = {"items": [], "total": 0, "cantidad_total": 0}

    return render(request, "tienda/carrito.html", {
        "carrito": carrito,
        "hay_sin_stock": any(i["sin_stock"] for i in carrito["items"]),
    })


@sesion_requerida
@require_POST
def carrito_agregar(request):
    try:
        cantidad = int(request.POST.get("cantidad", 1))
    except ValueError:
        cantidad = 1

    operar(
        request, "POST", "/carrito/items",
        {"producto_id": request.POST.get("producto_id", ""), "cantidad": cantidad},
        "Producto añadido al carrito.",
    )
    return destino(request, "catalogo")


@sesion_requerida
@require_POST
def carrito_actualizar(request, producto_id):
    try:
        cantidad = int(request.POST.get("cantidad", 1))
    except ValueError:
        cantidad = 1

    operar(
        request, "PUT", f"/carrito/items/{producto_id}",
        {"cantidad": cantidad},
        "Cantidad actualizada.",
    )
    return redirect("carrito")


@sesion_requerida
@require_POST
def carrito_eliminar(request, producto_id):
    operar(
        request, "DELETE", f"/carrito/items/{producto_id}",
        exito="Producto eliminado del carrito.",
    )
    return redirect("carrito")


@sesion_requerida
@require_POST
def carrito_vaciar(request):
    operar(request, "DELETE", "/carrito/", exito="Carrito vaciado.")
    return redirect("carrito")


@sesion_requerida
@require_POST
def carrito_confirmar(request):
    respuesta = api(request, "POST", "/carrito/confirmar")

    if respuesta.ok:
        request.session["carrito_n"] = 0
        messages.success(request, "¡Pedido confirmado! Puedes seguirlo aquí.")
        return redirect("mis_pedidos")

    messages.error(request, detalle_error(respuesta))
    return redirect("carrito")


# ---------- Mis pedidos ----------

@sesion_requerida
def mis_pedidos(request):
    respuesta = api(request, "GET", "/pedidos/mis-pedidos")

    if not respuesta.ok:
        messages.error(request, detalle_error(respuesta))
        return render(request, "tienda/mis_pedidos.html", {"compras": []})

    compras = {}

    for p in respuesta.json():
        clave = p.get("compra_id") or p["id"]
        compra = compras.setdefault(clave, {
            "orden": p["fecha"],
            "fecha": p["fecha"],
            "items": [],
            "total": 0,
        })

        try:
            compra["fecha"] = datetime.fromisoformat(p["fecha"])
        except ValueError:
            pass

        p["subtotal"] = p.get("precio_unitario", 0) * p["cantidad"]
        compra["items"].append(p)
        compra["total"] += p["subtotal"]

    lista = sorted(compras.values(), key=lambda c: c["orden"], reverse=True)

    return render(request, "tienda/mis_pedidos.html", {"compras": lista})
from django import template

register = template.Library()

ICONOS = {
    "laptops": "💻",
    "celulares": "📱",
    "audio": "🎧",
    "periféricos": "⌨️",
    "monitores": "🖥️",
    "gaming": "🎮",
    "almacenamiento": "💾",
    "accesorios": "🔌",
}

COLORES_ESTADO = {
    "registrado": "info",
    "enviado": "primary",
    "entregado": "success",
    "cancelado": "secondary",
}


@register.filter
def icono(categoria):
    return ICONOS.get(str(categoria).strip().lower(), "📦")


@register.filter
def color_estado(estado):
    return COLORES_ESTADO.get(estado, "dark")
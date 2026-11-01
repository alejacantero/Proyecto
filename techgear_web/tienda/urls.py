from django.urls import path
from . import views, views_admin as admin

urlpatterns = [
    path("", views.listar_productos, name="catalogo"),
    path("login/", views.iniciar_sesion, name="login"),
    path("registro/", views.registro, name="registro"),
    path("logout/", views.cerrar_sesion, name="logout"),
   

    # Panel de administración
    path("panel/", admin.admin_inicio, name="admin_inicio"),

    path("panel/productos/", admin.admin_productos, name="admin_productos"),
    path("panel/productos/nuevo/", admin.admin_producto_form, name="admin_producto_crear"),
    path("panel/productos/<str:producto_id>/editar/", admin.admin_producto_form, name="admin_producto_editar"),
    path("panel/productos/<str:producto_id>/eliminar/", admin.admin_producto_eliminar, name="admin_producto_eliminar"),

    path("panel/usuarios/", admin.admin_usuarios, name="admin_usuarios"),
    path("panel/usuarios/<str:usuario_id>/editar/", admin.admin_usuario_editar, name="admin_usuario_editar"),
    path("panel/usuarios/<str:usuario_id>/eliminar/", admin.admin_usuario_eliminar, name="admin_usuario_eliminar"),

    path("panel/pedidos/", admin.admin_pedidos, name="admin_pedidos"),
    path("panel/pedidos/nuevo/", admin.admin_pedido_crear, name="admin_pedido_crear"),
    path("panel/pedidos/<str:pedido_id>/estado/", admin.admin_pedido_estado, name="admin_pedido_estado"),
    path("panel/pedidos/<str:pedido_id>/eliminar/", admin.admin_pedido_eliminar, name="admin_pedido_eliminar"),
]
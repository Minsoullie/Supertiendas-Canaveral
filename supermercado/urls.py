from django.urls import path

from . import views

app_name = "supermercado"

urlpatterns = [
    path("", views.inicio, name="inicio"),

    # Clientes (CRUD)
    path("clientes/", views.clientes_lista, name="clientes"),
    path("clientes/nuevo/", views.cliente_nuevo, name="cliente_nuevo"),
    path("clientes/<int:pk>/editar/", views.cliente_editar, name="cliente_editar"),
    path("clientes/<int:pk>/eliminar/", views.cliente_eliminar, name="cliente_eliminar"),

    # Proveedores (CRUD)
    path("proveedores/", views.proveedores_lista, name="proveedores"),
    path("proveedores/nuevo/", views.proveedor_nuevo, name="proveedor_nuevo"),
    path("proveedores/<int:pk>/editar/", views.proveedor_editar, name="proveedor_editar"),
    path("proveedores/<int:pk>/eliminar/", views.proveedor_eliminar, name="proveedor_eliminar"),

    # Productos / Insumos (CRUD con eliminación lógica)
    path("productos/", views.productos_lista, name="productos"),
    path("productos/nuevo/", views.producto_nuevo, name="producto_nuevo"),
    path("productos/<int:pk>/editar/", views.producto_editar, name="producto_editar"),
    path("productos/<int:pk>/eliminar/", views.producto_eliminar, name="producto_eliminar"),

    # Inventario (días de stock)
    path("inventario/", views.inventario_lista, name="inventario"),
    path("inventario/<int:pk>/editar/", views.inventario_editar, name="inventario_editar"),

    # Facturas de venta (crear, consultar, anular)
    path("facturas/", views.facturas_lista, name="facturas"),
    path("facturas/nueva/", views.factura_nueva, name="factura_nueva"),
    path("facturas/<int:pk>/", views.factura_detalle, name="factura_detalle"),
    path("facturas/<int:pk>/anular/", views.factura_anular, name="factura_anular"),

    # Órdenes de pedido (crear, consultar, recibir, cancelar)
    path("pedidos/", views.pedidos_lista, name="pedidos"),
    path("pedidos/nuevo/", views.pedido_nuevo, name="pedido_nuevo"),
    path("pedidos/<int:pk>/", views.pedido_detalle, name="pedido_detalle"),
    path("pedidos/<int:pk>/recibir/", views.pedido_recibir, name="pedido_recibir"),
    path("pedidos/<int:pk>/cancelar/", views.pedido_cancelar, name="pedido_cancelar"),

    # Consultas SQL (20)
    path("consultas/", views.consultas_sql, name="consultas"),
]

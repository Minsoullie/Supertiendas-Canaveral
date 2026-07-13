"""Panel de administración (complementa la app web, no la reemplaza)."""
from django.contrib import admin

from .models import (
    Categoria, Cliente, Compra, DetalleCompra, DetalleOrden, Empleado, Empresa,
    Inventario, Marca, MetodoPago, Orden, Producto, Proveedor, ResolucionDian, Sede,
    TarjetaAmarilla,
)

admin.site.site_header = "Supertiendas Cañaveral S.A."
admin.site.site_title = "Supertiendas Cañaveral"
admin.site.index_title = "Administración de la base de datos"


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("id_cliente", "nombres", "apellidos", "tipo_documento", "numero_documento",
                    "ciudad", "tipo_cliente", "regimen_tributario", "habeas_data")
    list_filter = ("tipo_cliente", "tipo_documento", "regimen_tributario", "habeas_data", "ciudad")
    search_fields = ("nombres", "apellidos", "numero_documento", "email")


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("id_proveedor", "razon_social", "nit", "tipo_proveedor", "calificacion",
                    "tiempo_entrega_promedio", "condiciones_pago")
    list_filter = ("tipo_proveedor", "calificacion", "banco")
    search_fields = ("razon_social", "nit", "rut")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("id_producto", "nombre", "categoria", "marca", "proveedor",
                    "precio_venta", "categoria_iva", "iva", "activo")
    list_filter = ("activo", "categoria_iva", "categoria", "marca", "proveedor")
    search_fields = ("nombre", "codigo_barras")


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ("id_inventario", "producto", "sede", "cantidad_disponible",
                    "demanda_diaria", "dias_stock", "categoria_estado", "accion_recomendada")
    list_filter = ("sede",)

    @admin.display(description="Días de stock")
    def dias_stock(self, obj):
        return obj.dias_stock

    @admin.display(description="Estado")
    def categoria_estado(self, obj):
        return obj.categoria_estado

    @admin.display(description="Acción")
    def accion_recomendada(self, obj):
        return obj.accion_recomendada


class DetalleOrdenInline(admin.TabularInline):
    model = DetalleOrden
    extra = 0


@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ("numero_completo", "fecha_orden", "cliente", "sede", "metodo_pago",
                    "tipo_venta", "estado", "total")
    list_filter = ("estado", "tipo_venta", "sede")
    date_hierarchy = "fecha_orden"
    inlines = [DetalleOrdenInline]


class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 0


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ("id_compra", "fecha_compra", "proveedor", "sede", "lugar_entrega",
                    "estado", "total")
    list_filter = ("estado", "sede")
    inlines = [DetalleCompraInline]


admin.site.register([Empresa, ResolucionDian, Sede, Categoria, Marca, MetodoPago,
                     TarjetaAmarilla, Empleado])

from django import forms

from .models import (
    Cliente, Compra, DetalleCompra, DetalleOrden, Inventario, Producto, Proveedor,
)

TXT = {"class": "campo"}
NUM = {"class": "campo", "type": "number"}


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "tipo_documento", "numero_documento", "nombres", "apellidos", "tipo_cliente",
            "regimen_tributario", "representante_legal", "email", "telefono", "ciudad",
            "direccion_residencia", "direccion_operativa", "habeas_data",
        ]
        widgets = {
            "tipo_documento": forms.Select(attrs=TXT),
            "numero_documento": forms.TextInput(attrs=TXT),
            "nombres": forms.TextInput(attrs=TXT),
            "apellidos": forms.TextInput(attrs=TXT),
            "tipo_cliente": forms.Select(attrs=TXT),
            "regimen_tributario": forms.Select(attrs=TXT),
            "representante_legal": forms.TextInput(attrs=TXT),
            "email": forms.EmailInput(attrs=TXT),
            "telefono": forms.TextInput(attrs=TXT),
            "ciudad": forms.TextInput(attrs=TXT),
            "direccion_residencia": forms.TextInput(attrs=TXT),
            "direccion_operativa": forms.TextInput(attrs=TXT),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campo crítico protegido al editar (no se puede cambiar el documento)
        if self.instance and self.instance.pk:
            self.fields["numero_documento"].disabled = True
            self.fields["tipo_documento"].disabled = True
            self.fields["numero_documento"].help_text = (
                "Campo protegido: el documento no se puede modificar una vez registrado.")

    def clean(self):
        datos = super().clean()
        if datos.get("tipo_cliente") == "JURIDICO" and datos.get("tipo_documento") != "NIT":
            self.add_error("tipo_documento", "Una persona jurídica debe identificarse con NIT.")
        if not datos.get("habeas_data"):
            self.add_error("habeas_data",
                           "El cliente debe autorizar el tratamiento de datos (Ley 1581 de 2012).")
        return datos


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = [
            "tipo_documento", "nit", "razon_social", "rut", "regimen_tributario",
            "representante_legal", "ciudad", "direccion", "telefono", "email",
            "banco", "tipo_cuenta", "numero_cuenta",
            "tipo_proveedor", "tiempo_entrega_promedio", "condiciones_pago", "calificacion",
            "contacto_comercial", "contacto_cartera", "contacto_logistico", "habeas_data",
        ]
        widgets = {
            "tipo_documento": forms.Select(attrs=TXT),
            "nit": forms.TextInput(attrs=TXT),
            "razon_social": forms.TextInput(attrs=TXT),
            "rut": forms.TextInput(attrs=TXT),
            "regimen_tributario": forms.Select(attrs=TXT),
            "representante_legal": forms.TextInput(attrs=TXT),
            "ciudad": forms.TextInput(attrs=TXT),
            "direccion": forms.TextInput(attrs=TXT),
            "telefono": forms.TextInput(attrs=TXT),
            "email": forms.EmailInput(attrs=TXT),
            "banco": forms.TextInput(attrs=TXT),
            "tipo_cuenta": forms.Select(attrs=TXT),
            "numero_cuenta": forms.TextInput(attrs=TXT),
            "tipo_proveedor": forms.Select(attrs=TXT),
            "tiempo_entrega_promedio": forms.NumberInput(attrs={**NUM, "min": 1}),
            "condiciones_pago": forms.NumberInput(attrs={**NUM, "min": 0}),
            "calificacion": forms.NumberInput(attrs={**NUM, "min": 1, "max": 5}),
            "contacto_comercial": forms.TextInput(attrs=TXT),
            "contacto_cartera": forms.TextInput(attrs=TXT),
            "contacto_logistico": forms.TextInput(attrs=TXT),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["nit"].disabled = True     # campo crítico protegido
            self.fields["nit"].help_text = "Campo protegido: el NIT no se puede modificar."


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["codigo_barras", "nombre", "descripcion", "categoria", "marca", "proveedor",
                  "precio_venta", "unidad_medida", "categoria_iva", "activo"]
        widgets = {
            "codigo_barras": forms.TextInput(attrs=TXT),
            "nombre": forms.TextInput(attrs=TXT),
            "descripcion": forms.Textarea(attrs={**TXT, "rows": 2}),
            "categoria": forms.Select(attrs=TXT),
            "marca": forms.Select(attrs=TXT),
            "proveedor": forms.Select(attrs=TXT),
            "precio_venta": forms.NumberInput(attrs={**NUM, "min": 1, "step": "0.01"}),
            "unidad_medida": forms.Select(attrs=TXT),
            "categoria_iva": forms.Select(attrs=TXT),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restricción: no se puede registrar un producto sin proveedor previo
        self.fields["proveedor"].queryset = Proveedor.objects.order_by("razon_social")
        self.fields["proveedor"].empty_label = "— Seleccione un proveedor registrado —"
        self.fields["proveedor"].required = True
        if not Proveedor.objects.exists():
            self.fields["proveedor"].help_text = (
                "No hay proveedores registrados. Debe crear el proveedor primero.")
        if self.instance and self.instance.pk:
            self.fields["codigo_barras"].disabled = True

    def clean(self):
        from .models import TARIFA_POR_CATEGORIA
        datos = super().clean()
        cat = datos.get("categoria_iva")
        if cat:
            # La tarifa se deriva de la categoría: el usuario no la escribe a mano
            self.instance.iva = TARIFA_POR_CATEGORIA[cat]
        return datos


class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ["producto", "sede", "cantidad_disponible", "demanda_diaria", "stock_minimo"]
        widgets = {
            "producto": forms.Select(attrs=TXT),
            "sede": forms.Select(attrs=TXT),
            "cantidad_disponible": forms.NumberInput(attrs={**NUM, "min": 0}),
            "demanda_diaria": forms.NumberInput(attrs={**NUM, "min": "0.01", "step": "0.01"}),
            "stock_minimo": forms.NumberInput(attrs={**NUM, "min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["producto"].queryset = Producto.objects.filter(activo=True).order_by("nombre")
        if self.instance and self.instance.pk:
            self.fields["producto"].disabled = True
            self.fields["sede"].disabled = True


class FacturaForm(forms.ModelForm):
    """Cabecera de la factura. Solo se usa para CREAR (nunca para editar)."""
    class Meta:
        model = DetalleOrden.orden.field.related_model   # Orden
        fields = ["cliente", "sede", "empleado", "metodo_pago", "tipo_venta"]
        widgets = {
            "cliente": forms.Select(attrs=TXT),
            "sede": forms.Select(attrs=TXT),
            "empleado": forms.Select(attrs=TXT),
            "metodo_pago": forms.Select(attrs=TXT),
            "tipo_venta": forms.Select(attrs=TXT),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cliente"].queryset = Cliente.objects.order_by("nombres")
        self.fields["cliente"].empty_label = "— Seleccione un cliente registrado —"


class DetalleFacturaForm(forms.ModelForm):
    class Meta:
        model = DetalleOrden
        fields = ["producto", "cantidad"]
        widgets = {
            "producto": forms.Select(attrs=TXT),
            "cantidad": forms.NumberInput(attrs={**NUM, "min": 1, "value": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["producto"].queryset = Producto.objects.filter(activo=True).order_by("nombre")
        self.fields["producto"].empty_label = "— Seleccione un producto —"


class OrdenPedidoForm(forms.ModelForm):
    """Cabecera de la orden de pedido. El estado siempre arranca en PENDIENTE."""
    class Meta:
        model = Compra
        fields = ["proveedor", "sede", "lugar_entrega"]
        widgets = {
            "proveedor": forms.Select(attrs=TXT),
            "sede": forms.Select(attrs=TXT),
            "lugar_entrega": forms.TextInput(
                attrs={**TXT, "placeholder": "Ej: Bodega Central - Yumbo"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restricción: no se pueden registrar órdenes de proveedores no registrados
        self.fields["proveedor"].queryset = Proveedor.objects.order_by("razon_social")
        self.fields["proveedor"].empty_label = "— Seleccione un proveedor registrado —"


class DetallePedidoForm(forms.ModelForm):
    class Meta:
        model = DetalleCompra
        fields = ["producto", "cantidad", "precio_unitario"]
        widgets = {
            "producto": forms.Select(attrs=TXT),
            "cantidad": forms.NumberInput(attrs={**NUM, "min": 1, "max": 500, "value": 1}),
            "precio_unitario": forms.NumberInput(attrs={**NUM, "min": 1, "step": "0.01"}),
        }

    def __init__(self, proveedor=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Producto.objects.filter(activo=True)
        if proveedor is not None:
            qs = qs.filter(proveedor=proveedor)   # solo productos de ese proveedor
        self.fields["producto"].queryset = qs.order_by("nombre")
        self.fields["producto"].empty_label = "— Seleccione un producto —"

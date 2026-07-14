from datetime import date
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q


TIPO_DOCUMENTO = [("CC", "Cédula de ciudadanía"), ("CE", "Cédula de extranjería"),
                  ("NIT", "NIT"), ("PP", "Pasaporte"), ("TI", "Tarjeta de identidad")]
TIPO_CLIENTE = [("NATURAL", "Persona natural"), ("JURIDICO", "Persona jurídica")]
REGIMEN = [("RESPONSABLE", "Responsable de IVA (Ordinario)"),
           ("NO_RESPONSABLE", "No responsable de IVA (Simplificado)")]
ESTADO_TARJETA = [("ACTIVA", "Activa"), ("INACTIVA", "Inactiva"), ("BLOQUEADA", "Bloqueada")]
UNIDAD_MEDIDA = [("UND", "Unidad"), ("KG", "Kilogramo"), ("LT", "Litro"),
                 ("MT", "Metro"), ("GR", "Gramo"), ("ML", "Mililitro")]
TIPO_VENTA = [("PRESENCIAL", "Presencial"), ("ONLINE", "En línea")]
ESTADO_ORDEN = [("PENDIENTE", "Pendiente"), ("PAGADA", "Pagada"), ("ANULADA", "Anulada")]
ESTADO_COMPRA = [("PENDIENTE", "Pendiente"), ("RECIBIDA", "Recibida"), ("CANCELADA", "Cancelada")]
TIPO_PROVEEDOR = [("MATERIA_PRIMA", "Materia prima"), ("PRODUCTO_TERMINADO", "Producto terminado"),
                  ("EMPAQUES", "Empaques"), ("ASEO", "Aseo e insumos"), ("SERVICIOS", "Servicios")]
TIPO_CUENTA = [("AHORROS", "Ahorros"), ("CORRIENTE", "Corriente")]


CATEGORIA_IVA = [
    ("GENERAL", "General (19%)"),
    ("DIFERENCIAL", "Diferencial (5%)"),
    ("EXENTO", "Exento (0%)"),
    ("EXCLUIDO", "Excluido (no causa IVA)"),
]
TARIFA_POR_CATEGORIA = {"GENERAL": Decimal("19"), "DIFERENCIAL": Decimal("5"),
                        "EXENTO": Decimal("0"), "EXCLUIDO": Decimal("0")}


class Empresa(models.Model):
    """Datos del vendedor que deben aparecer en la Factura Electrónica de Venta."""
    id_empresa = models.AutoField(primary_key=True, db_column="idempresa")
    nit = models.CharField("NIT", max_length=20)
    razon_social = models.CharField("Razón social", max_length=150, db_column="razonsocial")
    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=80)
    telefono = models.CharField(max_length=20)
    email = models.CharField(max_length=120)
    sitio_web = models.CharField(max_length=120, db_column="sitioweb", blank=True)

    class Meta:
        db_table = "empresa"
        verbose_name_plural = "Empresa"
        constraints = [models.UniqueConstraint(fields=["nit"], name="uq_emp_nit")]

    def __str__(self):
        return self.razon_social


class ResolucionDian(models.Model):
    """Resolución de facturación electrónica autorizada por la DIAN."""
    id_resolucion = models.AutoField(primary_key=True, db_column="idresolucion")
    numero_resolucion = models.CharField(max_length=30, db_column="numeroresolucion")
    prefijo = models.CharField(max_length=10)
    rango_desde = models.IntegerField(db_column="rangodesde")
    rango_hasta = models.IntegerField(db_column="rangohasta")
    vigencia_desde = models.DateField(db_column="vigenciadesde")
    vigencia_hasta = models.DateField(db_column="vigenciahasta")

    class Meta:
        db_table = "resolucion_dian"
        verbose_name = "Resolución DIAN"
        verbose_name_plural = "Resoluciones DIAN"
        constraints = [
            models.UniqueConstraint(fields=["numero_resolucion"], name="uq_res_numero"),
            models.CheckConstraint(condition=Q(rango_hasta__gt=F("rango_desde")),
                                   name="chk_res_rango"),
            models.CheckConstraint(condition=Q(vigencia_hasta__gt=F("vigencia_desde")),
                                   name="chk_res_vigencia"),
        ]

    def __str__(self):
        return f"{self.prefijo} - Res. {self.numero_resolucion}"


class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True, db_column="idcliente")
    tipo_documento = models.CharField("Tipo de documento", max_length=20,
                                      db_column="tipodocumento", choices=TIPO_DOCUMENTO)
    numero_documento = models.CharField("Número de identificación", max_length=20,
                                        db_column="numerodocumento")
    nombres = models.CharField("Nombres / Razón social", max_length=80)
    apellidos = models.CharField("Apellidos / Sigla", max_length=80)
    tipo_cliente = models.CharField("Tipo de cliente", max_length=20, db_column="tipocliente",
                                    choices=TIPO_CLIENTE)
    regimen_tributario = models.CharField("Régimen tributario", max_length=20,
                                          db_column="regimentributario", choices=REGIMEN,
                                          default="NO_RESPONSABLE")
    representante_legal = models.CharField("Representante legal", max_length=120,
                                           db_column="representantelegal")
    habeas_data = models.BooleanField("Autoriza habeas data (Ley 1581 de 2012)",
                                      db_column="habeasdata", default=False)
    email = models.CharField(max_length=120)
    telefono = models.CharField("Teléfono / Celular", max_length=20)
    ciudad = models.CharField("Ciudad / Municipio", max_length=80)
    direccion_residencia = models.CharField("Dirección de residencia", max_length=200,
                                            db_column="direccionresidencia")
    direccion_operativa = models.CharField("Dirección operativa", max_length=200,
                                           db_column="direccionoperativa", blank=True, null=True)
    fecha_registro = models.DateField(db_column="fecharegistro", default=date.today)

    class Meta:
        db_table = "cliente"
        verbose_name_plural = "Clientes"
        constraints = [
            models.UniqueConstraint(fields=["numero_documento"], name="uq_cli_documento"),
            models.UniqueConstraint(fields=["email"], name="uq_cli_email"),
            models.CheckConstraint(condition=Q(tipo_documento__in=["CC", "CE", "NIT", "PP", "TI"]),
                                   name="chk_cli_tipodoc"),
            models.CheckConstraint(condition=Q(tipo_cliente__in=["NATURAL", "JURIDICO"]),
                                   name="chk_cli_tipocliente"),
            models.CheckConstraint(condition=Q(regimen_tributario__in=["RESPONSABLE",
                                                                       "NO_RESPONSABLE"]),
                                   name="chk_cli_regimen"),
            # Una persona jurídica se identifica con NIT
            models.CheckConstraint(
                condition=~Q(tipo_cliente="JURIDICO") | Q(tipo_documento="NIT"),
                name="chk_cli_juridico_nit"),
        ]
        indexes = [models.Index(fields=["numero_documento"], name="idx_cliente_documento")]

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()

    def __str__(self):
        return self.nombre_completo


class Sede(models.Model):
    id_sede = models.AutoField(primary_key=True, db_column="idsede")
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=80)
    departamento = models.CharField(max_length=80)
    telefono = models.CharField(max_length=20)
    horario_apertura = models.TimeField("Horario de apertura", db_column="horarioapertura")
    horario_cierre = models.TimeField("Horario de cierre", db_column="horariocierre")

    class Meta:
        db_table = "sede"
        verbose_name_plural = "Sedes"
        constraints = [
            models.UniqueConstraint(fields=["nombre"], name="uq_sede_nombre"),
            models.CheckConstraint(condition=Q(horario_cierre__gt=F("horario_apertura")),
                                   name="chk_sede_horario"),
        ]

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True, db_column="idcategoria")
    nombre = models.CharField(max_length=80)
    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "categoria"
        verbose_name_plural = "Categorías"
        constraints = [models.UniqueConstraint(fields=["nombre"], name="uq_cat_nombre")]

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    id_marca = models.AutoField(primary_key=True, db_column="idmarca")
    nombre = models.CharField(max_length=80)
    es_marca_propia = models.BooleanField("¿Es marca propia?", db_column="esmarcapropia",
                                          default=False)

    class Meta:
        db_table = "marca"
        verbose_name_plural = "Marcas"
        constraints = [models.UniqueConstraint(fields=["nombre"], name="uq_marca_nombre")]

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True, db_column="idproveedor")
    # --- identificación (los mismos datos del cliente) ---
    tipo_documento = models.CharField("Tipo de documento", max_length=20,
                                      db_column="tipodocumento", choices=TIPO_DOCUMENTO,
                                      default="NIT")
    nit = models.CharField("NIT / Documento", max_length=20)
    razon_social = models.CharField("Razón social", max_length=150, db_column="razonsocial")
    rut = models.CharField("Número del RUT", max_length=30)
    regimen_tributario = models.CharField("Régimen tributario", max_length=20,
                                          db_column="regimentributario", choices=REGIMEN,
                                          default="RESPONSABLE")
    representante_legal = models.CharField("Representante legal", max_length=120,
                                           db_column="representantelegal")
    habeas_data = models.BooleanField("Autoriza habeas data (Ley 1581 de 2012)",
                                      db_column="habeasdata", default=True)
    ciudad = models.CharField("Ciudad / Municipio", max_length=80)
    direccion = models.CharField("Dirección operativa", max_length=200)
    telefono = models.CharField(max_length=20)
    email = models.CharField(max_length=120)
    # --- certificación bancaria ---
    banco = models.CharField(max_length=60)
    tipo_cuenta = models.CharField("Tipo de cuenta", max_length=15, db_column="tipocuenta",
                                   choices=TIPO_CUENTA, default="CORRIENTE")
    numero_cuenta = models.CharField("Número de cuenta", max_length=30, db_column="numerocuenta")
    # --- operación ---
    tipo_proveedor = models.CharField("Tipo de proveedor", max_length=25,
                                      db_column="tipoproveedor", choices=TIPO_PROVEEDOR)
    tiempo_entrega_promedio = models.IntegerField(
        "Tiempo de entrega promedio (días)", db_column="tiempoentregapromedio", default=7)
    condiciones_pago = models.IntegerField("Condiciones de pago (días)",
                                           db_column="condicionespago", default=30)
    calificacion = models.IntegerField(
        "Calificación (1 a 5)", default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)])
    # --- tres contactos ---
    contacto_comercial = models.CharField("Contacto comercial", max_length=120,
                                          db_column="contactocomercial")
    contacto_cartera = models.CharField("Contacto de cartera / pagos", max_length=120,
                                        db_column="contactocartera")
    contacto_logistico = models.CharField("Contacto logístico", max_length=120,
                                          db_column="contactologistico")

    class Meta:
        db_table = "proveedor"
        verbose_name_plural = "Proveedores"
        constraints = [
            models.UniqueConstraint(fields=["nit"], name="uq_prov_nit"),
            models.UniqueConstraint(fields=["email"], name="uq_prov_email"),
            models.CheckConstraint(condition=Q(calificacion__gte=1) & Q(calificacion__lte=5),
                                   name="chk_prov_calificacion"),
            models.CheckConstraint(condition=Q(tiempo_entrega_promedio__gt=0),
                                   name="chk_prov_entrega"),
            models.CheckConstraint(condition=Q(condiciones_pago__gte=0), name="chk_prov_pago"),
            models.CheckConstraint(condition=Q(tipo_cuenta__in=["AHORROS", "CORRIENTE"]),
                                   name="chk_prov_tipocuenta"),
        ]

    def __str__(self):
        return self.razon_social


class MetodoPago(models.Model):
    id_metodo_pago = models.AutoField(primary_key=True, db_column="idmetodopago")
    nombre = models.CharField(max_length=60)
    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "metodo_pago"
        verbose_name = "Método de pago"
        verbose_name_plural = "Métodos de pago"
        constraints = [models.UniqueConstraint(fields=["nombre"], name="uq_mp_nombre")]

    def __str__(self):
        return self.nombre


class TarjetaAmarilla(models.Model):
    """Programa de fidelización de la cadena."""
    id_tarjeta = models.AutoField(primary_key=True, db_column="idtarjeta")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column="idcliente",
                                related_name="tarjetas")
    numero_tarjeta = models.CharField(max_length=20, db_column="numerotarjeta")
    fecha_emision = models.DateField(db_column="fechaemision", default=date.today)
    puntos_acumulados = models.IntegerField(db_column="puntosacumulados", default=0)
    estado = models.CharField(max_length=15, choices=ESTADO_TARJETA, default="ACTIVA")

    class Meta:
        db_table = "tarjeta_amarilla"
        verbose_name = "Tarjeta Amarilla"
        verbose_name_plural = "Tarjetas Amarillas"
        constraints = [
            models.UniqueConstraint(fields=["numero_tarjeta"], name="uq_tar_numero"),
            models.CheckConstraint(condition=Q(puntos_acumulados__gte=0), name="chk_tar_puntos"),
            models.CheckConstraint(condition=Q(estado__in=["ACTIVA", "INACTIVA", "BLOQUEADA"]),
                                   name="chk_tar_estado"),
        ]

    def __str__(self):
        return self.numero_tarjeta


class Empleado(models.Model):
    id_empleado = models.AutoField(primary_key=True, db_column="idempleado")
    sede = models.ForeignKey(Sede, on_delete=models.RESTRICT, db_column="idsede",
                             related_name="empleados")
    numero_documento = models.CharField(max_length=20, db_column="numerodocumento")
    nombres = models.CharField(max_length=80)
    apellidos = models.CharField(max_length=80)
    cargo = models.CharField(max_length=60)
    salario = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_ingreso = models.DateField(db_column="fechaingreso", default=date.today)

    class Meta:
        db_table = "empleado"
        verbose_name_plural = "Empleados"
        constraints = [
            models.UniqueConstraint(fields=["numero_documento"], name="uq_emp_documento"),
            models.CheckConstraint(condition=Q(salario__gt=0), name="chk_emp_salario"),
        ]

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class Producto(models.Model):
    """
    Producto / insumo del catálogo.

    Reglas del enunciado:
      * No se puede registrar un producto sin un PROVEEDOR previamente registrado
        (FK obligatoria con ON DELETE RESTRICT).
      * La eliminación es LÓGICA (campo `activo`) para no perder el histórico.
      * `dias_stock` NO se almacena: se calcula (ver Inventario.dias_stock).
    """
    id_producto = models.AutoField(primary_key=True, db_column="idproducto")
    categoria = models.ForeignKey(Categoria, on_delete=models.RESTRICT, db_column="idcategoria",
                                  related_name="productos")
    marca = models.ForeignKey(Marca, on_delete=models.RESTRICT, db_column="idmarca",
                              related_name="productos")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.RESTRICT, db_column="idproveedor",
                                  related_name="productos",
                                  help_text="Obligatorio: el proveedor debe existir previamente.")
    codigo_barras = models.CharField("Código de barras", max_length=30, db_column="codigobarras")
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(null=True, blank=True)
    precio_venta = models.DecimalField("Precio de venta", max_digits=12, decimal_places=2,
                                       db_column="precioventa")
    unidad_medida = models.CharField("Unidad de medida", max_length=20, db_column="unidadmedida",
                                     choices=UNIDAD_MEDIDA)
    categoria_iva = models.CharField("Categoría de IVA", max_length=15, db_column="categoriaiva",
                                     choices=CATEGORIA_IVA, default="GENERAL")
    iva = models.DecimalField("Tarifa de IVA (%)", max_digits=5, decimal_places=2, default=19)
    activo = models.BooleanField("Activo", default=True,
                                 help_text="Desmarcar equivale a una eliminación lógica.")

    class Meta:
        db_table = "producto"
        verbose_name_plural = "Productos"
        constraints = [
            models.UniqueConstraint(fields=["codigo_barras"], name="uq_prod_barras"),
            models.CheckConstraint(condition=Q(precio_venta__gt=0), name="chk_prod_precio"),
            models.CheckConstraint(
                condition=Q(unidad_medida__in=["UND", "KG", "LT", "MT", "GR", "ML"]),
                name="chk_prod_unidad"),
            models.CheckConstraint(condition=Q(iva__in=[0, 5, 19]), name="chk_prod_iva"),
            # La tarifa debe ser coherente con la categoría de IVA declarada
            models.CheckConstraint(
                condition=(Q(categoria_iva="GENERAL", iva=19)
                           | Q(categoria_iva="DIFERENCIAL", iva=5)
                           | Q(categoria_iva="EXENTO", iva=0)
                           | Q(categoria_iva="EXCLUIDO", iva=0)),
                name="chk_prod_iva_categoria"),
        ]
        indexes = [
            models.Index(fields=["categoria"], name="idx_producto_categoria"),
            models.Index(fields=["proveedor"], name="idx_producto_proveedor"),
            models.Index(fields=["nombre"], name="idx_producto_nombre"),
        ]

    @property
    def causa_iva(self):
        """Los productos EXCLUIDOS no causan impuesto (el sistema no calcula nada)."""
        return self.categoria_iva != "EXCLUIDO"

    def __str__(self):
        return self.nombre


class Inventario(models.Model):
    """
    Existencias de un producto en una sede.

    IMPORTANTE: los "días de stock" NO se almacenan (lo prohíbe el enunciado);
    se calculan como  inventario_actual / demanda_diaria.
    """
    id_inventario = models.AutoField(primary_key=True, db_column="idinventario")
    producto = models.ForeignKey(Producto, on_delete=models.RESTRICT, db_column="idproducto",
                                 related_name="inventarios")
    sede = models.ForeignKey(Sede, on_delete=models.RESTRICT, db_column="idsede",
                             related_name="inventarios")
    cantidad_disponible = models.IntegerField("Inventario actual", db_column="cantidaddisponible",
                                              default=0)
    demanda_diaria = models.DecimalField("Demanda diaria (unidades/día)", max_digits=10,
                                         decimal_places=2, db_column="demandadiaria",
                                         default=Decimal("1.00"))
    stock_minimo = models.IntegerField("Stock mínimo", db_column="stockminimo", default=5)
    fecha_actualizacion = models.DateTimeField(db_column="fechaactualizacion", auto_now=True)

    class Meta:
        db_table = "inventario"
        verbose_name_plural = "Inventario"
        constraints = [
            models.UniqueConstraint(fields=["producto", "sede"], name="uq_inv_prod_sede"),
            models.CheckConstraint(condition=Q(cantidad_disponible__gte=0),
                                   name="chk_inv_cantidad"),
            models.CheckConstraint(condition=Q(stock_minimo__gte=0), name="chk_inv_stock_min"),
            models.CheckConstraint(condition=Q(demanda_diaria__gt=0), name="chk_inv_demanda"),
        ]
        indexes = [models.Index(fields=["sede"], name="idx_inventario_sede")]

    # --- Días de stock: CALCULADO, nunca almacenado -------------------------
    @property
    def dias_stock(self):
        if not self.demanda_diaria or self.demanda_diaria <= 0:
            return Decimal("0")
        return (Decimal(self.cantidad_disponible) / self.demanda_diaria).quantize(Decimal("0.1"))

    @property
    def categoria_estado(self):
        """AGOTADO / CRÍTICO / ALERTA / SEGURO, según la tabla del enunciado."""
        d = self.dias_stock
        if self.cantidad_disponible == 0 or d == 0:
            return "AGOTADO"
        if d < 5:
            return "CRITICO"
        if d <= 15:
            return "ALERTA"
        return "SEGURO"

    @property
    def accion_recomendada(self):
        return {
            "AGOTADO": "Pedido inmediato",
            "CRITICO": "Pedido de emergencia",
            "ALERTA": "Realizar pedido normal",
            "SEGURO": "Mantener monitoreo",
        }[self.categoria_estado]

    def __str__(self):
        return f"{self.producto} @ {self.sede}"


class Orden(models.Model):
    """
    Factura Electrónica de Venta.

    Una vez guardada NO debe ser editable ni eliminable (normativa de facturación
    electrónica). La aplicación solo permite ANULARLA, dejando el rastro intacto.
    """
    id_orden = models.AutoField(primary_key=True, db_column="idorden")
    resolucion = models.ForeignKey(ResolucionDian, on_delete=models.RESTRICT,
                                   db_column="idresolucion", related_name="ordenes")
    prefijo = models.CharField(max_length=10)
    numero_factura = models.IntegerField("Consecutivo DIAN", db_column="numerofactura")
    cliente = models.ForeignKey(Cliente, on_delete=models.RESTRICT, db_column="idcliente",
                                related_name="ordenes")
    empleado = models.ForeignKey(Empleado, on_delete=models.RESTRICT, db_column="idempleado",
                                 related_name="ordenes")
    sede = models.ForeignKey(Sede, on_delete=models.RESTRICT, db_column="idsede",
                             related_name="ordenes")
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.RESTRICT,
                                    db_column="idmetodopago", related_name="ordenes")
    fecha_orden = models.DateTimeField("Fecha y hora de generación", db_column="fechaorden")
    fecha_expedicion = models.DateTimeField("Fecha y hora de expedición",
                                            db_column="fechaexpedicion", null=True, blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    iva = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2)
    tipo_venta = models.CharField("Tipo de venta", max_length=20, db_column="tipoventa",
                                  choices=TIPO_VENTA, default="PRESENCIAL")
    estado = models.CharField(max_length=20, choices=ESTADO_ORDEN, default="PENDIENTE")
    cufe = models.CharField("CUFE", max_length=96, blank=True, null=True)

    class Meta:
        db_table = "orden"
        verbose_name = "Factura de venta"
        verbose_name_plural = "Facturas de venta"
        constraints = [
            models.UniqueConstraint(fields=["prefijo", "numero_factura"], name="uq_ord_factura"),
            models.CheckConstraint(condition=Q(tipo_venta__in=["PRESENCIAL", "ONLINE"]),
                                   name="chk_ord_tipo"),
            models.CheckConstraint(condition=Q(estado__in=["PENDIENTE", "PAGADA", "ANULADA"]),
                                   name="chk_ord_estado"),
            models.CheckConstraint(condition=Q(total=F("subtotal") + F("iva")),
                                   name="chk_ord_total"),
            models.CheckConstraint(condition=Q(subtotal__gte=0) & Q(iva__gte=0),
                                   name="chk_ord_valores"),
        ]
        indexes = [
            models.Index(fields=["fecha_orden"], name="idx_orden_fecha"),
            models.Index(fields=["sede"], name="idx_orden_sede"),
            models.Index(fields=["cliente"], name="idx_orden_cliente"),
            models.Index(fields=["estado"], name="idx_orden_estado"),
        ]

    @property
    def numero_completo(self):
        return f"{self.prefijo}-{self.numero_factura}"

    def __str__(self):
        return f"Factura {self.numero_completo}"


class Compra(models.Model):
    """
    Orden de Pedido a un proveedor.

    Reglas del enunciado: no se puede crear sin proveedor registrado, la cantidad
    mínima es 1, y el estado inicia SIEMPRE en PENDIENTE.
    Cuando pasa a RECIBIDA, un trigger de PL/pgSQL suma las unidades al inventario.
    """
    id_compra = models.AutoField(primary_key=True, db_column="idcompra")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.RESTRICT, db_column="idproveedor",
                                  related_name="compras")
    sede = models.ForeignKey(Sede, on_delete=models.RESTRICT, db_column="idsede",
                             related_name="compras")
    fecha_compra = models.DateField("Fecha de pedido", db_column="fechacompra", default=date.today)
    lugar_entrega = models.CharField("Lugar de entrega (bodega)", max_length=150,
                                     db_column="lugarentrega")
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_COMPRA, default="PENDIENTE")

    class Meta:
        db_table = "compra"
        verbose_name = "Orden de pedido"
        verbose_name_plural = "Órdenes de pedido"
        constraints = [
            models.CheckConstraint(condition=Q(total__gte=0), name="chk_comp_total"),
            models.CheckConstraint(condition=Q(estado__in=["PENDIENTE", "RECIBIDA", "CANCELADA"]),
                                   name="chk_comp_estado"),
        ]
        indexes = [models.Index(fields=["proveedor"], name="idx_compra_proveedor")]

    def __str__(self):
        return f"Orden de pedido #{self.id_compra}"


class DetalleOrden(models.Model):
    """Ítem de la factura. El IVA se discrimina POR CADA ÍTEM (exigencia DIAN)."""
    id_detalle_orden = models.AutoField(primary_key=True, db_column="iddetalleorden")
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, db_column="idorden",
                              related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.RESTRICT, db_column="idproducto",
                                 related_name="detalles_orden")
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2,
                                          db_column="preciounitario")
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    iva_porcentaje = models.DecimalField("IVA (%)", max_digits=5, decimal_places=2,
                                         db_column="ivaporcentaje", default=0)
    iva_valor = models.DecimalField("Valor del IVA", max_digits=14, decimal_places=2,
                                    db_column="ivavalor", default=0)

    class Meta:
        db_table = "detalle_orden"
        verbose_name = "Detalle de factura"
        verbose_name_plural = "Detalles de factura"
        constraints = [
            models.UniqueConstraint(fields=["orden", "producto"], name="uq_dord_prod_orden"),
            models.CheckConstraint(condition=Q(cantidad__gt=0), name="chk_dord_cantidad"),
            models.CheckConstraint(condition=Q(precio_unitario__gt=0), name="chk_dord_precio"),
            models.CheckConstraint(condition=Q(subtotal=F("precio_unitario") * F("cantidad")),
                                   name="chk_dord_subtotal"),
        ]
        indexes = [models.Index(fields=["producto"], name="idx_detalleorden_producto")]

    @property
    def total_linea(self):
        return self.subtotal + self.iva_valor

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"


class DetalleCompra(models.Model):
    """Ítem de la orden de pedido. Cantidad mínima 1, máximo 500 (regla del negocio)."""
    id_detalle_compra = models.AutoField(primary_key=True, db_column="iddetallecompra")
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, db_column="idcompra",
                               related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.RESTRICT, db_column="idproducto",
                                 related_name="detalles_compra")
    cantidad = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(500)])
    precio_unitario = models.DecimalField("Costo unitario", max_digits=12, decimal_places=2,
                                          db_column="preciounitario")

    class Meta:
        db_table = "detalle_compra"
        verbose_name = "Detalle de orden de pedido"
        verbose_name_plural = "Detalles de orden de pedido"
        constraints = [
            models.UniqueConstraint(fields=["compra", "producto"], name="uq_dcomp_prod_comp"),
            # Regla del enunciado: mínimo 1, máximo definido por el negocio (500)
            models.CheckConstraint(condition=Q(cantidad__gte=1) & Q(cantidad__lte=500),
                                   name="chk_dcomp_cantidad"),
            models.CheckConstraint(condition=Q(precio_unitario__gt=0), name="chk_dcomp_precio"),
        ]

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"

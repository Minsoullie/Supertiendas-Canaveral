"""
Vistas de la aplicación web de Supertiendas Cañaveral.

CRUD completo de las cinco entidades que exige el enunciado:
  Clientes · Proveedores · Productos/Insumos · Facturas · Órdenes de Pedido

Reglas de integridad implementadas:
  * No se elimina un cliente o proveedor con facturas / órdenes asociadas.
  * Los productos usan ELIMINACIÓN LÓGICA (activo = False).
  * Las facturas y las órdenes de pedido NO son editables ni eliminables:
    solo se pueden anular / cancelar (el rastro contable queda intacto).
  * No se registra un producto ni una orden sin un proveedor previo.
"""

from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.db import connection, transaction
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .consultas import CONSULTAS, ejecutar
from .forms import (
    ClienteForm, DetalleFacturaForm, DetallePedidoForm, FacturaForm, InventarioForm,
    OrdenPedidoForm, ProductoForm, ProveedorForm,
)
from .models import (
    TARIFA_POR_CATEGORIA, Cliente, Compra, DetalleCompra, DetalleOrden, Empleado, Empresa,
    Inventario, MetodoPago, Orden, Producto, Proveedor, ResolucionDian, Sede,
)

CENT = Decimal("0.01")


def money(x):
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)


# ===========================================================================
#  INICIO / DASHBOARD
# ===========================================================================
def inicio(request):
    pagadas = Orden.objects.filter(estado="PAGADA")
    agg = pagadas.aggregate(ingresos=Sum("total"), n=Count("id_orden"))

    inventarios = Inventario.objects.select_related("producto", "sede")
    conteo = {"AGOTADO": 0, "CRITICO": 0, "ALERTA": 0, "SEGURO": 0}
    for inv in inventarios:
        conteo[inv.categoria_estado] += 1

    # Ventas por mes (para el gráfico de barras del dashboard)
    with connection.cursor() as cur:
        cur.execute("""
            SELECT TO_CHAR(DATE_TRUNC('month', fechaOrden), 'YYYY-MM') AS mes,
                   SUM(total) AS ingresos
            FROM ORDEN
            WHERE estado = 'PAGADA'
            GROUP BY DATE_TRUNC('month', fechaOrden)
            ORDER BY mes
        """)
        filas = cur.fetchall()
    maximo = max([float(f[1]) for f in filas], default=1) or 1
    serie = [{"mes": f[0][5:], "valor": float(f[1]),
              "pct": round(100 * float(f[1]) / maximo, 1)} for f in filas]

    contexto = {
        "kpis": [
            ("Ingresos facturados", f"$ {agg['ingresos'] or 0:,.0f}"),
            ("Facturas pagadas", f"{agg['n'] or 0:,}"),
            ("Clientes", f"{Cliente.objects.count():,}"),
            ("Proveedores", f"{Proveedor.objects.count():,}"),
            ("Productos activos", f"{Producto.objects.filter(activo=True).count():,}"),
            ("Sedes", f"{Sede.objects.count():,}"),
        ],
        "conteo": conteo,
        "serie": serie,
        "alertas": [i for i in inventarios if i.categoria_estado in ("AGOTADO", "CRITICO")][:8],
        "empresa": Empresa.objects.first(),
    }
    return render(request, "supermercado/inicio.html", contexto)


# ===========================================================================
#  CLIENTES  (CRUD)
# ===========================================================================
def clientes_lista(request):
    busqueda = request.GET.get("buscar", "").strip()
    clientes = Cliente.objects.all()
    if busqueda:
        clientes = clientes.filter(
            Q(nombres__icontains=busqueda) | Q(apellidos__icontains=busqueda)
            | Q(numero_documento__icontains=busqueda) | Q(email__icontains=busqueda)
            | Q(ciudad__icontains=busqueda)
        ).distinct()
    clientes = clientes.annotate(n_facturas=Count("ordenes")).order_by("-id_cliente")[:150]
    return render(request, "supermercado/clientes_lista.html",
                  {"clientes": clientes, "buscar": busqueda})


def cliente_nuevo(request):
    formulario = ClienteForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        cli = formulario.save()
        messages.success(request, f"Cliente «{cli.nombre_completo}» registrado correctamente.")
        return redirect("supermercado:clientes")
    return render(request, "supermercado/form.html", {
        "form": formulario, "titulo": "Registrar cliente",
        "volver": "supermercado:clientes",
        "ayuda": "El cliente debe autorizar el tratamiento de datos (Ley 1581 de 2012).",
    })


def cliente_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    formulario = ClienteForm(request.POST or None, instance=cliente)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Cliente modificado correctamente.")
        return redirect("supermercado:clientes")
    return render(request, "supermercado/form.html", {
        "form": formulario, "titulo": f"Editar cliente: {cliente.nombre_completo}",
        "volver": "supermercado:clientes",
        "ayuda": "El tipo y el número de documento están protegidos y no se pueden modificar.",
    })


def cliente_eliminar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    # Integridad referencial: no se borra un cliente con facturas
    if cliente.ordenes.exists():
        messages.error(
            request,
            f"No se puede eliminar «{cliente.nombre_completo}»: tiene "
            f"{cliente.ordenes.count()} factura(s) asociada(s).")
        return redirect("supermercado:clientes")
    if request.method == "POST":
        nombre = cliente.nombre_completo
        cliente.delete()
        messages.success(request, f"Cliente «{nombre}» eliminado.")
        return redirect("supermercado:clientes")
    return render(request, "supermercado/confirmar.html", {
        "objeto": cliente.nombre_completo, "titulo": "Eliminar cliente",
        "volver": "supermercado:clientes",
    })


# ===========================================================================
#  PROVEEDORES  (CRUD)
# ===========================================================================
def proveedores_lista(request):
    busqueda = request.GET.get("buscar", "").strip()
    proveedores = Proveedor.objects.all()
    if busqueda:
        proveedores = proveedores.filter(
            Q(razon_social__icontains=busqueda) | Q(nit__icontains=busqueda)
            | Q(tipo_proveedor__icontains=busqueda) | Q(ciudad__icontains=busqueda)
        ).distinct()
    proveedores = proveedores.annotate(
        n_productos=Count("productos", distinct=True),
        n_pedidos=Count("compras", distinct=True)).order_by("razon_social")
    return render(request, "supermercado/proveedores_lista.html",
                  {"proveedores": proveedores, "buscar": busqueda})


def proveedor_nuevo(request):
    formulario = ProveedorForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        prov = formulario.save()
        messages.success(request, f"Proveedor «{prov.razon_social}» registrado correctamente.")
        return redirect("supermercado:proveedores")
    return render(request, "supermercado/form.html", {
        "form": formulario, "titulo": "Registrar proveedor",
        "volver": "supermercado:proveedores",
        "ayuda": "El RUT y la certificación bancaria son obligatorios para programar pagos.",
    })


def proveedor_editar(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    formulario = ProveedorForm(request.POST or None, instance=proveedor)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Proveedor modificado correctamente.")
        return redirect("supermercado:proveedores")
    return render(request, "supermercado/form.html", {
        "form": formulario, "titulo": f"Editar proveedor: {proveedor.razon_social}",
        "volver": "supermercado:proveedores",
        "ayuda": "El NIT está protegido y no se puede modificar.",
    })


def proveedor_eliminar(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if proveedor.compras.exists() or proveedor.productos.exists():
        messages.error(
            request,
            f"No se puede eliminar «{proveedor.razon_social}»: tiene "
            f"{proveedor.productos.count()} producto(s) y {proveedor.compras.count()} "
            f"orden(es) de pedido asociadas.")
        return redirect("supermercado:proveedores")
    if request.method == "POST":
        nombre = proveedor.razon_social
        proveedor.delete()
        messages.success(request, f"Proveedor «{nombre}» eliminado.")
        return redirect("supermercado:proveedores")
    return render(request, "supermercado/confirmar.html", {
        "objeto": proveedor.razon_social, "titulo": "Eliminar proveedor",
        "volver": "supermercado:proveedores",
    })


# ===========================================================================
#  PRODUCTOS / INSUMOS  (CRUD con eliminación lógica)
# ===========================================================================
def productos_lista(request):
    busqueda = request.GET.get("buscar", "").strip()
    ver_inactivos = request.GET.get("inactivos") == "1"
    productos = Producto.objects.select_related("categoria", "marca", "proveedor")
    if not ver_inactivos:
        productos = productos.filter(activo=True)
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | Q(codigo_barras__icontains=busqueda)
            | Q(categoria__nombre__icontains=busqueda) | Q(marca__nombre__icontains=busqueda)
            | Q(proveedor__razon_social__icontains=busqueda)
        ).distinct()
    return render(request, "supermercado/productos_lista.html", {
        "productos": productos.order_by("nombre")[:200], "buscar": busqueda,
        "inactivos": ver_inactivos, "hay_proveedores": Proveedor.objects.exists(),
    })


def producto_nuevo(request):
    if not Proveedor.objects.exists():
        messages.error(request, "No hay proveedores registrados. Registre primero un proveedor: "
                                "no se puede crear un producto sin proveedor.")
        return redirect("supermercado:proveedor_nuevo")
    formulario = ProductoForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        prod = formulario.save()
        messages.success(request, f"Producto «{prod.nombre}» registrado correctamente.")
        return redirect("supermercado:productos")
    return render(request, "supermercado/form.html", {
        "form": formulario, "titulo": "Registrar producto / insumo",
        "volver": "supermercado:productos",
        "ayuda": "El proveedor es obligatorio y debe estar registrado previamente. "
                 "La tarifa de IVA se deriva de la categoría seleccionada.",
    })


def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    formulario = ProductoForm(request.POST or None, instance=producto)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Producto modificado correctamente.")
        return redirect("supermercado:productos")
    return render(request, "supermercado/form.html", {
        "form": formulario, "titulo": f"Editar producto: {producto.nombre}",
        "volver": "supermercado:productos",
        "ayuda": "El código de barras está protegido y no se puede modificar.",
    })


def producto_eliminar(request, pk):
    """Eliminación LÓGICA: no se borra la fila, se marca como inactiva."""
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        producto.activo = not producto.activo
        producto.save(update_fields=["activo"])
        estado = "reactivado" if producto.activo else "desactivado (eliminación lógica)"
        messages.success(request, f"Producto «{producto.nombre}» {estado}.")
        return redirect("supermercado:productos")
    return render(request, "supermercado/confirmar.html", {
        "objeto": producto.nombre,
        "titulo": "Reactivar producto" if not producto.activo else "Desactivar producto",
        "volver": "supermercado:productos",
        "nota": "No se borra el registro físico: se conserva el histórico de movimientos "
                "de inventario (eliminación lógica).",
    })


# ===========================================================================
#  INVENTARIO  (días de stock CALCULADOS, nunca almacenados)
# ===========================================================================
def inventario_lista(request):
    busqueda = request.GET.get("buscar", "").strip()
    estado = request.GET.get("estado", "")
    inventarios = Inventario.objects.select_related("producto", "sede", "producto__proveedor")
    if busqueda:
        inventarios = inventarios.filter(
            Q(producto__nombre__icontains=busqueda) | Q(sede__nombre__icontains=busqueda)
        ).distinct()
    filas = list(inventarios.order_by("producto__nombre"))
    if estado:
        filas = [i for i in filas if i.categoria_estado == estado]
    resumen = {"AGOTADO": 0, "CRITICO": 0, "ALERTA": 0, "SEGURO": 0}
    for i in inventarios:
        resumen[i.categoria_estado] += 1
    return render(request, "supermercado/inventario_lista.html", {
        "inventarios": filas[:200], "buscar": busqueda, "estado": estado, "resumen": resumen,
    })


def inventario_editar(request, pk):
    inv = get_object_or_404(Inventario, pk=pk)
    formulario = InventarioForm(request.POST or None, instance=inv)
    if request.method == "POST" and formulario.is_valid():
        formulario.save()
        messages.success(request, "Inventario actualizado.")
        return redirect("supermercado:inventario")
    return render(request, "supermercado/form.html", {
        "form": formulario, "titulo": f"Inventario: {inv.producto} — {inv.sede}",
        "volver": "supermercado:inventario",
        "ayuda": "Los días de stock NO se almacenan: se calculan como "
                 "inventario actual ÷ demanda diaria.",
    })


# ===========================================================================
#  FACTURAS DE VENTA  (crear + consultar + anular; NUNCA editar ni eliminar)
# ===========================================================================
def facturas_lista(request):
    busqueda = request.GET.get("buscar", "").strip()
    facturas = Orden.objects.select_related("cliente", "sede", "metodo_pago")
    if busqueda:
        facturas = facturas.filter(
            Q(numero_factura__icontains=busqueda) | Q(cliente__nombres__icontains=busqueda)
            | Q(cliente__apellidos__icontains=busqueda)
            | Q(cliente__numero_documento__icontains=busqueda)
        ).distinct()
    return render(request, "supermercado/facturas_lista.html", {
        "facturas": facturas.order_by("-id_orden")[:150], "buscar": busqueda,
    })


def factura_detalle(request, pk):
    factura = get_object_or_404(
        Orden.objects.select_related("cliente", "sede", "empleado", "metodo_pago", "resolucion"),
        pk=pk)
    return render(request, "supermercado/factura_detalle.html", {
        "f": factura,
        "detalles": factura.detalles.select_related("producto"),
        "empresa": Empresa.objects.first(),
    })


@transaction.atomic
def factura_nueva(request):
    if not Cliente.objects.exists() or not Producto.objects.filter(activo=True).exists():
        messages.error(request, "Se necesitan clientes y productos activos para facturar.")
        return redirect("supermercado:facturas")

    formulario = FacturaForm(request.POST or None)
    linea = DetalleFacturaForm()

    if request.method == "POST":
        productos_ids = request.POST.getlist("producto")
        cantidades = request.POST.getlist("cantidad")
        pares = [(p, c) for p, c in zip(productos_ids, cantidades) if p and c]

        if not pares:
            messages.error(request, "La factura debe tener al menos 1 producto.")
        elif formulario.is_valid():
            resolucion = ResolucionDian.objects.first()
            if resolucion is None:
                messages.error(request, "No hay una resolución DIAN configurada.")
                return redirect("supermercado:facturas")

            ultimo = (Orden.objects.filter(prefijo=resolucion.prefijo)
                      .order_by("-numero_factura").first())
            consecutivo = (ultimo.numero_factura + 1) if ultimo else resolucion.rango_desde

            ahora = timezone.now()
            factura = formulario.save(commit=False)
            factura.resolucion = resolucion
            factura.prefijo = resolucion.prefijo
            factura.numero_factura = consecutivo
            factura.fecha_orden = ahora
            factura.fecha_expedicion = ahora
            factura.estado = "PAGADA"
            factura.subtotal = Decimal("0.00")
            factura.iva = Decimal("0.00")
            factura.total = Decimal("0.00")
            factura.save()

            subtotal = Decimal("0.00")
            iva_total = Decimal("0.00")
            vistos = set()
            for pid, cant in pares:
                if pid in vistos:            # evita violar UNIQUE (orden, producto)
                    continue
                vistos.add(pid)
                producto = Producto.objects.get(pk=pid)
                cantidad = max(1, int(cant))
                linea_sub = money(producto.precio_venta * cantidad)
                # Los productos EXCLUIDOS no causan IVA: el sistema no calcula nada
                tarifa = producto.iva if producto.causa_iva else Decimal("0")
                linea_iva = money(linea_sub * tarifa / Decimal(100))
                DetalleOrden.objects.create(
                    orden=factura, producto=producto, cantidad=cantidad,
                    precio_unitario=producto.precio_venta, subtotal=linea_sub,
                    iva_porcentaje=tarifa, iva_valor=linea_iva)
                subtotal += linea_sub
                iva_total += linea_iva

            factura.subtotal = subtotal
            factura.iva = iva_total
            factura.total = subtotal + iva_total     # CHECK: total = subtotal + iva
            factura.cufe = f"CUFE-{factura.prefijo}{factura.numero_factura:08d}"
            factura.save()

            messages.success(request, f"Factura {factura.numero_completo} generada. "
                                      f"El stock se descontó automáticamente (trigger PL/pgSQL).")
            return redirect("supermercado:factura_detalle", pk=factura.pk)

    return render(request, "supermercado/factura_nueva.html", {
        "form": formulario, "linea": linea,
        "productos": Producto.objects.filter(activo=True).order_by("nombre"),
    })


def factura_anular(request, pk):
    """Las facturas no se eliminan ni se editan: solo se anulan."""
    factura = get_object_or_404(Orden, pk=pk)
    if request.method == "POST":
        if factura.estado == "ANULADA":
            messages.warning(request, "La factura ya estaba anulada.")
        else:
            factura.estado = "ANULADA"
            factura.save(update_fields=["estado"])
            messages.success(request, f"Factura {factura.numero_completo} anulada. "
                                      f"El registro se conserva para la auditoría.")
        return redirect("supermercado:facturas")
    return render(request, "supermercado/confirmar.html", {
        "objeto": f"Factura {factura.numero_completo}", "titulo": "Anular factura",
        "volver": "supermercado:facturas",
        "nota": "Según la normativa de facturación electrónica, una factura no se puede "
                "eliminar ni editar. Solo se anula, y el rastro queda inalterable.",
    })


# ===========================================================================
#  ÓRDENES DE PEDIDO  (crear + consultar + recibir; NUNCA editar ni eliminar)
# ===========================================================================
def pedidos_lista(request):
    busqueda = request.GET.get("buscar", "").strip()
    pedidos = Compra.objects.select_related("proveedor", "sede")
    if busqueda:
        pedidos = pedidos.filter(
            Q(id_compra__icontains=busqueda) | Q(proveedor__razon_social__icontains=busqueda)
            | Q(proveedor__nit__icontains=busqueda) | Q(lugar_entrega__icontains=busqueda)
        ).distinct()
    return render(request, "supermercado/pedidos_lista.html", {
        "pedidos": pedidos.order_by("-id_compra")[:150], "buscar": busqueda,
    })


def pedido_detalle(request, pk):
    pedido = get_object_or_404(Compra.objects.select_related("proveedor", "sede"), pk=pk)
    return render(request, "supermercado/pedido_detalle.html", {
        "p": pedido, "detalles": pedido.detalles.select_related("producto"),
        "empresa": Empresa.objects.first(),
    })


@transaction.atomic
def pedido_nuevo(request):
    if not Proveedor.objects.exists():
        messages.error(request, "No se puede crear una orden de pedido sin proveedores "
                                "registrados previamente.")
        return redirect("supermercado:proveedor_nuevo")

    proveedor_id = request.POST.get("proveedor") or request.GET.get("proveedor")
    proveedor = Proveedor.objects.filter(pk=proveedor_id).first() if proveedor_id else None
    formulario = OrdenPedidoForm(request.POST or None)

    if request.method == "POST":
        productos_ids = request.POST.getlist("producto")
        cantidades = request.POST.getlist("cantidad")
        costos = request.POST.getlist("precio_unitario")
        items = [(p, c, k) for p, c, k in zip(productos_ids, cantidades, costos) if p and c and k]

        if not items:
            messages.error(request, "La orden debe tener al menos 1 producto.")
        elif formulario.is_valid():
            pedido = formulario.save(commit=False)
            pedido.estado = "PENDIENTE"          # siempre inicia en PENDIENTE
            pedido.total = Decimal("0.00")
            pedido.save()

            total = Decimal("0.00")
            vistos = set()
            for pid, cant, costo in items:
                if pid in vistos:
                    continue
                vistos.add(pid)
                producto = Producto.objects.get(pk=pid)
                cantidad = min(500, max(1, int(cant)))     # regla: entre 1 y 500
                precio = money(costo)
                DetalleCompra.objects.create(compra=pedido, producto=producto,
                                             cantidad=cantidad, precio_unitario=precio)
                total += money(precio * cantidad)

            pedido.total = total
            pedido.save(update_fields=["total"])
            messages.success(request, f"Orden de pedido #{pedido.pk} creada en estado PENDIENTE.")
            return redirect("supermercado:pedido_detalle", pk=pedido.pk)

    productos = Producto.objects.filter(activo=True)
    if proveedor:
        productos = productos.filter(proveedor=proveedor)
    return render(request, "supermercado/pedido_nuevo.html", {
        "form": formulario, "productos": productos.order_by("nombre"),
        "proveedor_sel": proveedor,
        "proveedores": Proveedor.objects.order_by("razon_social"),
    })


def pedido_recibir(request, pk):
    """
    Marca la orden como RECIBIDA.
    El trigger de PL/pgSQL `trg_compra_recibida` suma las unidades al inventario
    de la sede automáticamente: la aplicación no toca el stock a mano.
    """
    pedido = get_object_or_404(Compra, pk=pk)
    if request.method == "POST":
        if pedido.estado != "PENDIENTE":
            messages.warning(request, f"La orden ya está {pedido.get_estado_display().lower()}.")
        else:
            pedido.estado = "RECIBIDA"
            pedido.save(update_fields=["estado"])
            messages.success(
                request,
                f"Orden #{pedido.pk} recibida. El stock se actualizó automáticamente "
                f"mediante el trigger de PL/pgSQL.")
        return redirect("supermercado:pedido_detalle", pk=pedido.pk)
    return render(request, "supermercado/confirmar.html", {
        "objeto": f"Orden de pedido #{pedido.pk}", "titulo": "Marcar como RECIBIDA",
        "volver": "supermercado:pedidos",
        "nota": "Al recibirla, el trigger de PL/pgSQL sumará automáticamente las unidades "
                "al inventario de la sede.",
    })


def pedido_cancelar(request, pk):
    pedido = get_object_or_404(Compra, pk=pk)
    if request.method == "POST":
        if pedido.estado == "RECIBIDA":
            messages.error(request, "No se puede cancelar una orden ya recibida.")
        else:
            pedido.estado = "CANCELADA"
            pedido.save(update_fields=["estado"])
            messages.success(request, f"Orden #{pedido.pk} cancelada.")
        return redirect("supermercado:pedidos")
    return render(request, "supermercado/confirmar.html", {
        "objeto": f"Orden de pedido #{pedido.pk}", "titulo": "Cancelar orden de pedido",
        "volver": "supermercado:pedidos",
        "nota": "Las órdenes de pedido no se eliminan: se cancelan para conservar el rastro.",
    })


# ===========================================================================
#  CONSULTAS SQL  (20 consultas: 10 básicas + 10 complejas)
# ===========================================================================
def consultas_sql(request):
    grupo = request.GET.get("grupo", "todas")
    seleccion = [c for c in CONSULTAS
                 if grupo == "todas" or c["grupo"] == grupo]
    resultados = []
    for c in seleccion:
        columnas, filas = ejecutar(c, connection)
        resultados.append({**c, "columnas": columnas, "filas": filas[:12],
                           "total_filas": len(filas), "sql": c["sql"].strip()})
    return render(request, "supermercado/consultas.html",
                  {"resultados": resultados, "grupo": grupo})

"""
Alinea el esquema con el DDL del Avance 2/3 y agrega el RETO OPCIONAL del enunciado.

Contenido:
  1. Nombres de las llaves primarias y foráneas del DDL, con sus reglas
     ON DELETE / ON UPDATE a nivel del motor (Django las maneja solo en Python).
  2. RETO 2 — Tres VISTAS de consultas recurrentes; una guarda los días de stock.
  3. RETO 3 — Gestión automática del inventario con PL/pgSQL:
       * Al marcar una ORDEN DE PEDIDO como RECIBIDA, se suman las unidades al stock.
       * Al facturar una venta, se descuentan las unidades del stock de esa sede.
"""

from django.db import migrations

PK_POR_TABLA = {
    "empresa": "pk_empresa",
    "resolucion_dian": "pk_resolucion",
    "cliente": "pk_cliente",
    "sede": "pk_sede",
    "categoria": "pk_categoria",
    "marca": "pk_marca",
    "proveedor": "pk_proveedor",
    "metodo_pago": "pk_metodo_pago",
    "tarjeta_amarilla": "pk_tarjeta",
    "empleado": "pk_empleado",
    "producto": "pk_producto",
    "inventario": "pk_inventario",
    "orden": "pk_orden",
    "compra": "pk_compra",
    "detalle_orden": "pk_detalle_orden",
    "detalle_compra": "pk_detalle_compra",
}
TABLAS = list(PK_POR_TABLA)

# (nombre, tabla, columna, tabla_ref, columna_ref, on_delete)
LLAVES_FORANEAS = [
    ("fk_tar_cliente",     "tarjeta_amarilla", "idcliente",    "cliente",         "idcliente",    "CASCADE"),
    ("fk_emp_sede",        "empleado",         "idsede",       "sede",            "idsede",       "RESTRICT"),
    ("fk_prod_categoria",  "producto",         "idcategoria",  "categoria",       "idcategoria",  "RESTRICT"),
    ("fk_prod_marca",      "producto",         "idmarca",      "marca",           "idmarca",      "RESTRICT"),
    ("fk_prod_proveedor",  "producto",         "idproveedor",  "proveedor",       "idproveedor",  "RESTRICT"),
    ("fk_inv_producto",    "inventario",       "idproducto",   "producto",        "idproducto",   "RESTRICT"),
    ("fk_inv_sede",        "inventario",       "idsede",       "sede",            "idsede",       "RESTRICT"),
    ("fk_ord_resolucion",  "orden",            "idresolucion", "resolucion_dian", "idresolucion", "RESTRICT"),
    ("fk_ord_cliente",     "orden",            "idcliente",    "cliente",         "idcliente",    "RESTRICT"),
    ("fk_ord_empleado",    "orden",            "idempleado",   "empleado",        "idempleado",   "RESTRICT"),
    ("fk_ord_sede",        "orden",            "idsede",       "sede",            "idsede",       "RESTRICT"),
    ("fk_ord_metodopago",  "orden",            "idmetodopago", "metodo_pago",     "idmetodopago", "RESTRICT"),
    ("fk_comp_proveedor",  "compra",           "idproveedor",  "proveedor",       "idproveedor",  "RESTRICT"),
    ("fk_comp_sede",       "compra",           "idsede",       "sede",            "idsede",       "RESTRICT"),
    ("fk_dord_orden",      "detalle_orden",    "idorden",      "orden",           "idorden",      "CASCADE"),
    ("fk_dord_producto",   "detalle_orden",    "idproducto",   "producto",        "idproducto",   "RESTRICT"),
    ("fk_dcomp_compra",    "detalle_compra",   "idcompra",     "compra",          "idcompra",     "CASCADE"),
    ("fk_dcomp_producto",  "detalle_compra",   "idproducto",   "producto",        "idproducto",   "RESTRICT"),
]

# ---------------------------------------------------------------------------
# 1. Restricciones con los nombres y las reglas del DDL
# ---------------------------------------------------------------------------
def sql_restricciones():
    lineas = [f"ALTER TABLE {t} RENAME CONSTRAINT {t}_pkey TO {pk};"
              for t, pk in PK_POR_TABLA.items()]
    lista = ", ".join(f"'{t}'" for t in TABLAS)
    lineas.append(f"""
DO $$
DECLARE r RECORD;
BEGIN
    FOR r IN SELECT conrelid::regclass AS tabla, conname
             FROM pg_constraint
             WHERE contype = 'f'
               AND connamespace = 'public'::regnamespace
               AND conrelid::regclass::text IN ({lista})
    LOOP
        EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', r.tabla, r.conname);
    END LOOP;
END $$;""")
    for nombre, tabla, col, ref_t, ref_c, on_del in LLAVES_FORANEAS:
        lineas.append(
            f"ALTER TABLE {tabla} ADD CONSTRAINT {nombre} FOREIGN KEY ({col}) "
            f"REFERENCES {ref_t} ({ref_c}) ON DELETE {on_del} ON UPDATE CASCADE;")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# 2. RETO — Tres vistas de consultas recurrentes
# ---------------------------------------------------------------------------
VISTAS = """
-- VISTA 1: Días de stock por producto y sede, con su categoría de estado y la
-- acción recomendada. Los días NO se almacenan en ninguna tabla: la vista los calcula.
CREATE OR REPLACE VIEW vw_dias_stock AS
SELECT i.idInventario,
       p.idProducto,
       p.nombre                                            AS producto,
       pr.razonSocial                                      AS proveedor,
       pr.tiempoEntregaPromedio                            AS dias_entrega_proveedor,
       s.idSede,
       s.nombre                                            AS sede,
       i.cantidadDisponible                                AS inventario_actual,
       i.demandaDiaria                                     AS demanda_diaria,
       ROUND(i.cantidadDisponible / i.demandaDiaria, 1)    AS dias_stock,
       CASE
         WHEN i.cantidadDisponible = 0                          THEN 'AGOTADO'
         WHEN i.cantidadDisponible / i.demandaDiaria < 5        THEN 'CRITICO'
         WHEN i.cantidadDisponible / i.demandaDiaria <= 15      THEN 'ALERTA'
         ELSE 'SEGURO'
       END                                                 AS categoria_estado,
       CASE
         WHEN i.cantidadDisponible = 0                          THEN 'Pedido inmediato'
         WHEN i.cantidadDisponible / i.demandaDiaria < 5        THEN 'Pedido de emergencia'
         WHEN i.cantidadDisponible / i.demandaDiaria <= 15      THEN 'Realizar pedido normal'
         ELSE 'Mantener monitoreo'
       END                                                 AS accion_recomendada
FROM INVENTARIO i
JOIN PRODUCTO  p  ON p.idProducto  = i.idProducto
JOIN PROVEEDOR pr ON pr.idProveedor = p.idProveedor
JOIN SEDE      s  ON s.idSede      = i.idSede
WHERE p.activo = TRUE;

-- VISTA 2: Resumen de ventas por sede y mes (consulta recurrente de gerencia).
CREATE OR REPLACE VIEW vw_ventas_mensuales AS
SELECT s.idSede,
       s.nombre                                            AS sede,
       s.ciudad,
       DATE_TRUNC('month', o.fechaOrden)::date             AS mes,
       COUNT(o.idOrden)                                    AS facturas,
       SUM(o.subtotal)                                     AS base_gravable,
       SUM(o.iva)                                          AS iva_recaudado,
       SUM(o.total)                                        AS ingresos,
       ROUND(AVG(o.total), 0)                              AS ticket_promedio
FROM ORDEN o
JOIN SEDE  s ON s.idSede = o.idSede
WHERE o.estado = 'PAGADA'
GROUP BY s.idSede, s.nombre, s.ciudad, DATE_TRUNC('month', o.fechaOrden);

-- VISTA 3: Desempeño de proveedores (cumplimiento y monto comprado).
CREATE OR REPLACE VIEW vw_desempeno_proveedores AS
SELECT pr.idProveedor,
       pr.razonSocial                                      AS proveedor,
       pr.nit,
       pr.tipoProveedor                                    AS tipo,
       pr.calificacion,
       pr.tiempoEntregaPromedio                            AS dias_entrega,
       pr.condicionesPago                                  AS dias_pago,
       COUNT(DISTINCT p.idProducto)                        AS productos_suministrados,
       COUNT(DISTINCT co.idCompra)                         AS pedidos,
       COUNT(DISTINCT co.idCompra) FILTER (WHERE co.estado = 'RECIBIDA') AS pedidos_recibidos,
       COALESCE(SUM(DISTINCT co.total), 0)                 AS monto_comprado
FROM PROVEEDOR pr
LEFT JOIN PRODUCTO p ON p.idProveedor  = pr.idProveedor
LEFT JOIN COMPRA  co ON co.idProveedor = pr.idProveedor
GROUP BY pr.idProveedor, pr.razonSocial, pr.nit, pr.tipoProveedor, pr.calificacion,
         pr.tiempoEntregaPromedio, pr.condicionesPago;
"""

VISTAS_REVERSE = """
DROP VIEW IF EXISTS vw_desempeno_proveedores;
DROP VIEW IF EXISTS vw_ventas_mensuales;
DROP VIEW IF EXISTS vw_dias_stock;
"""


# ---------------------------------------------------------------------------
# 3. RETO — Gestión automática del inventario con PL/pgSQL
# ---------------------------------------------------------------------------
TRIGGERS = """
-- ---------------------------------------------------------------------------
-- Al pasar una ORDEN DE PEDIDO a RECIBIDA, sumar sus unidades al inventario.
-- Si el producto aún no existe en esa sede, se crea la fila de inventario.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_compra_recibida()
RETURNS TRIGGER AS $$
DECLARE d RECORD;
BEGIN
    IF NEW.estado = 'RECIBIDA' AND OLD.estado <> 'RECIBIDA' THEN
        FOR d IN SELECT idProducto, cantidad
                 FROM DETALLE_COMPRA
                 WHERE idCompra = NEW.idCompra
        LOOP
            INSERT INTO INVENTARIO (idProducto, idSede, cantidadDisponible,
                                    demandaDiaria, stockMinimo, fechaActualizacion)
            VALUES (d.idProducto, NEW.idSede, d.cantidad, 1.00, 5, NOW())
            ON CONFLICT (idProducto, idSede) DO UPDATE
                SET cantidadDisponible = INVENTARIO.cantidadDisponible + EXCLUDED.cantidadDisponible,
                    fechaActualizacion = NOW();
        END LOOP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_compra_recibida ON COMPRA;
CREATE TRIGGER trg_compra_recibida
    AFTER UPDATE ON COMPRA
    FOR EACH ROW
    EXECUTE FUNCTION fn_compra_recibida();


-- ---------------------------------------------------------------------------
-- Al facturar una venta, descontar las unidades del inventario de esa sede.
-- Nunca deja el stock en negativo (la restricción CHECK lo impediría).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_venta_descuenta_stock()
RETURNS TRIGGER AS $$
DECLARE v_sede INT;
BEGIN
    SELECT idSede INTO v_sede FROM ORDEN WHERE idOrden = NEW.idOrden;

    UPDATE INVENTARIO
       SET cantidadDisponible = GREATEST(cantidadDisponible - NEW.cantidad, 0),
           fechaActualizacion = NOW()
     WHERE idProducto = NEW.idProducto
       AND idSede     = v_sede;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_venta_descuenta_stock ON DETALLE_ORDEN;
CREATE TRIGGER trg_venta_descuenta_stock
    AFTER INSERT ON DETALLE_ORDEN
    FOR EACH ROW
    EXECUTE FUNCTION fn_venta_descuenta_stock();
"""

TRIGGERS_REVERSE = """
DROP TRIGGER IF EXISTS trg_venta_descuenta_stock ON DETALLE_ORDEN;
DROP FUNCTION IF EXISTS fn_venta_descuenta_stock();
DROP TRIGGER IF EXISTS trg_compra_recibida ON COMPRA;
DROP FUNCTION IF EXISTS fn_compra_recibida();
"""


def sql_restricciones_reverse():
    lineas = []
    for nombre, tabla, col, ref_t, ref_c, _ in LLAVES_FORANEAS:
        lineas.append(f"ALTER TABLE {tabla} DROP CONSTRAINT {nombre};")
        lineas.append(f"ALTER TABLE {tabla} ADD CONSTRAINT {nombre}_simple "
                      f"FOREIGN KEY ({col}) REFERENCES {ref_t} ({ref_c});")
    for t, pk in PK_POR_TABLA.items():
        lineas.append(f"ALTER TABLE {t} RENAME CONSTRAINT {pk} TO {t}_pkey;")
    return "\n".join(lineas)


class Migration(migrations.Migration):

    dependencies = [("supermercado", "0001_initial")]

    operations = [
        migrations.RunSQL(sql=sql_restricciones(), reverse_sql=sql_restricciones_reverse()),
        migrations.RunSQL(sql=VISTAS, reverse_sql=VISTAS_REVERSE),
        migrations.RunSQL(sql=TRIGGERS, reverse_sql=TRIGGERS_REVERSE),
    ]

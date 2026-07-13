-- ============================================================================
-- Supertiendas Cañaveral S.A. — RETO OPCIONAL
--   1. Índices sobre las tablas más consultadas (ver el DDL)
--   2. Tres VISTAS de consultas recurrentes (una guarda los días de stock)
--   3. Gestión automática del inventario con PL/pgSQL (triggers)
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 2. VISTAS
-- ---------------------------------------------------------------------------

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


-- ---------------------------------------------------------------------------
-- 3. GESTIÓN AUTOMÁTICA DE INVENTARIO (PL/pgSQL)
-- ---------------------------------------------------------------------------

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


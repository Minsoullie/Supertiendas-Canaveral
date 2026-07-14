
--   Consultas 1-10  : aspectos BÁSICOS del negocio
--   Consultas 11-20 : aspectos COMPLEJOS (JOIN, subconsultas, ventanas)

-- ----------------------------------------------------------------------------
-- CONSULTA 1 [BÁSICA]: Catálogo de productos activos por categoría
-- Negocio: ¿Cuántas referencias maneja cada categoría y a qué precio promedio?
-- Técnica: JOIN + GROUP BY + AVG
-- ----------------------------------------------------------------------------
SELECT c.nombre                     AS categoria,
       COUNT(p.idProducto)          AS productos,
       ROUND(AVG(p.precioVenta), 0) AS precio_promedio,
       MIN(p.precioVenta)           AS precio_minimo,
       MAX(p.precioVenta)           AS precio_maximo
FROM PRODUCTO p
JOIN CATEGORIA c ON c.idCategoria = p.idCategoria
WHERE p.activo = TRUE
GROUP BY c.idCategoria, c.nombre
ORDER BY productos DESC;

-- ----------------------------------------------------------------------------
-- CONSULTA 2 [BÁSICA]: Clientes por ciudad y tipo
-- Negocio: ¿Dónde está la base de clientes y qué proporción son empresas?
-- Técnica: GROUP BY + COUNT FILTER
-- ----------------------------------------------------------------------------
SELECT ciudad,
       COUNT(*)                                          AS total_clientes,
       COUNT(*) FILTER (WHERE tipoCliente = 'NATURAL')   AS naturales,
       COUNT(*) FILTER (WHERE tipoCliente = 'JURIDICO')  AS juridicos,
       COUNT(*) FILTER (WHERE habeasData = TRUE)         AS autorizan_datos
FROM CLIENTE
GROUP BY ciudad
ORDER BY total_clientes DESC;

-- ----------------------------------------------------------------------------
-- CONSULTA 3 [BÁSICA]: Facturación por sede
-- Negocio: ¿Qué tienda vende más? Base del ranking de desempeño.
-- Técnica: JOIN + GROUP BY + SUM/AVG
-- ----------------------------------------------------------------------------
SELECT s.nombre               AS sede,
       s.ciudad,
       COUNT(o.idOrden)       AS facturas,
       SUM(o.total)           AS ingresos,
       ROUND(AVG(o.total), 0) AS ticket_promedio
FROM SEDE s
JOIN ORDEN o ON o.idSede = s.idSede
WHERE o.estado = 'PAGADA'
GROUP BY s.idSede, s.nombre, s.ciudad
ORDER BY ingresos DESC;

-- ----------------------------------------------------------------------------
-- CONSULTA 4 [BÁSICA]: Productos por proveedor
-- Negocio: ¿De quién depende el surtido? Concentración de proveedores.
-- Técnica: JOIN + GROUP BY
-- ----------------------------------------------------------------------------
SELECT pr.razonSocial          AS proveedor,
       pr.tipoProveedor        AS tipo,
       pr.calificacion,
       pr.tiempoEntregaPromedio AS dias_entrega,
       COUNT(p.idProducto)     AS productos
FROM PROVEEDOR pr
JOIN PRODUCTO p ON p.idProveedor = pr.idProveedor
GROUP BY pr.idProveedor, pr.razonSocial, pr.tipoProveedor,
         pr.calificacion, pr.tiempoEntregaPromedio
ORDER BY productos DESC;

-- ----------------------------------------------------------------------------
-- CONSULTA 5 [BÁSICA]: Métodos de pago más usados
-- Negocio: ¿En qué medios de pago conviene invertir (Nequi, PSE, tarjetas)?
-- Técnica: JOIN + GROUP BY + COUNT FILTER
-- ----------------------------------------------------------------------------
SELECT mp.nombre                                          AS metodo_pago,
       COUNT(*)                                           AS facturas,
       COUNT(*) FILTER (WHERE o.tipoVenta = 'PRESENCIAL') AS presencial,
       COUNT(*) FILTER (WHERE o.tipoVenta = 'ONLINE')     AS online,
       SUM(o.total)                                       AS monto_total
FROM ORDEN o
JOIN METODO_PAGO mp ON mp.idMetodoPago = o.idMetodoPago
WHERE o.estado = 'PAGADA'
GROUP BY mp.idMetodoPago, mp.nombre
ORDER BY facturas DESC;

-- ----------------------------------------------------------------------------
-- CONSULTA 6 [BÁSICA]: Recaudo de IVA por tarifa
-- Negocio: Cuánto IVA se recauda por cada tarifa vigente (19%, 5%, 0%).
-- Técnica: GROUP BY + SUM sobre el IVA discriminado por ítem
-- ----------------------------------------------------------------------------
SELECT d.ivaPorcentaje       AS tarifa_iva,
       COUNT(*)              AS items_facturados,
       SUM(d.subtotal)       AS base_gravable,
       SUM(d.ivaValor)       AS iva_recaudado
FROM DETALLE_ORDEN d
JOIN ORDEN o ON o.idOrden = d.idOrden
WHERE o.estado = 'PAGADA'
GROUP BY d.ivaPorcentaje
ORDER BY d.ivaPorcentaje DESC;

-- ----------------------------------------------------------------------------
-- CONSULTA 7 [BÁSICA]: Empleados y nómina por sede
-- Negocio: Costo de personal y tamaño del equipo por tienda.
-- Técnica: JOIN + GROUP BY + SUM/AVG
-- ----------------------------------------------------------------------------
SELECT s.nombre                AS sede,
       COUNT(e.idEmpleado)     AS empleados,
       ROUND(AVG(e.salario), 0) AS salario_promedio,
       SUM(e.salario)          AS nomina_mensual
FROM SEDE s
JOIN EMPLEADO e ON e.idSede = s.idSede
GROUP BY s.idSede, s.nombre
ORDER BY nomina_mensual DESC;

-- ----------------------------------------------------------------------------
-- CONSULTA 8 [BÁSICA]: Estado de las órdenes de pedido
-- Negocio: ¿Cuánto dinero está comprometido en pedidos pendientes?
-- Técnica: GROUP BY + agregados
-- ----------------------------------------------------------------------------
SELECT estado,
       COUNT(*)               AS ordenes,
       SUM(total)             AS monto_total,
       ROUND(AVG(total), 0)   AS monto_promedio
FROM COMPRA
GROUP BY estado
ORDER BY monto_total DESC;

-- ----------------------------------------------------------------------------
-- CONSULTA 9 [BÁSICA]: Tarjeta Amarilla: estado del programa de fidelización
-- Negocio: ¿Cuántas tarjetas activas hay y cuántos puntos se han acumulado?
-- Técnica: GROUP BY + SUM/AVG
-- ----------------------------------------------------------------------------
SELECT estado,
       COUNT(*)                        AS tarjetas,
       SUM(puntosAcumulados)           AS puntos_totales,
       ROUND(AVG(puntosAcumulados), 0) AS puntos_promedio
FROM TARJETA_AMARILLA
GROUP BY estado
ORDER BY tarjetas DESC;

-- ----------------------------------------------------------------------------
-- CONSULTA 10 [BÁSICA]: Ventas por mes (estacionalidad)
-- Negocio: Meses pico y tendencia, para planear inventario y personal.
-- Técnica: DATE_TRUNC + GROUP BY
-- ----------------------------------------------------------------------------
SELECT TO_CHAR(DATE_TRUNC('month', fechaOrden), 'YYYY-MM') AS anio_mes,
       COUNT(*)                                            AS facturas,
       SUM(total)                                          AS ingresos,
       ROUND(AVG(total), 0)                                AS ticket_promedio
FROM ORDEN
WHERE estado = 'PAGADA'
GROUP BY DATE_TRUNC('month', fechaOrden)
ORDER BY anio_mes;

-- ----------------------------------------------------------------------------
-- CONSULTA 11 [COMPLEJA]: Top 10 productos más vendidos
-- Negocio: Productos estrella: negociación con proveedores y ubicación en góndola.
-- Técnica: 5 JOIN + COUNT(DISTINCT) + GROUP BY
-- ----------------------------------------------------------------------------
SELECT p.nombre                  AS producto,
       c.nombre                  AS categoria,
       m.nombre                  AS marca,
       pr.razonSocial            AS proveedor,
       SUM(d.cantidad)           AS unidades,
       SUM(d.subtotal)           AS ingresos,
       COUNT(DISTINCT d.idOrden) AS facturas
FROM DETALLE_ORDEN d
JOIN PRODUCTO  p  ON p.idProducto  = d.idProducto
JOIN CATEGORIA c  ON c.idCategoria = p.idCategoria
JOIN MARCA     m  ON m.idMarca     = p.idMarca
JOIN PROVEEDOR pr ON pr.idProveedor = p.idProveedor
JOIN ORDEN     o  ON o.idOrden     = d.idOrden
WHERE o.estado = 'PAGADA'
GROUP BY p.idProducto, p.nombre, c.nombre, m.nombre, pr.razonSocial
ORDER BY unidades DESC
LIMIT 10;

-- ----------------------------------------------------------------------------
-- CONSULTA 12 [COMPLEJA]: Participación de ingresos por categoría
-- Negocio: Qué líneas sostienen la facturación (regla de Pareto).
-- Técnica: Función de ventana SOBRE un agregado
-- ----------------------------------------------------------------------------
SELECT c.nombre                                                         AS categoria,
       SUM(d.cantidad)                                                  AS unidades,
       SUM(d.subtotal)                                                  AS ingresos,
       ROUND(100.0 * SUM(d.subtotal) / SUM(SUM(d.subtotal)) OVER (), 2) AS participacion_pct,
       ROUND(100.0 * SUM(SUM(d.subtotal)) OVER (ORDER BY SUM(d.subtotal) DESC)
             / SUM(SUM(d.subtotal)) OVER (), 2)                         AS acumulado_pct
FROM DETALLE_ORDEN d
JOIN PRODUCTO  p ON p.idProducto  = d.idProducto
JOIN CATEGORIA c ON c.idCategoria = p.idCategoria
JOIN ORDEN     o ON o.idOrden     = d.idOrden
WHERE o.estado = 'PAGADA'
GROUP BY c.idCategoria, c.nombre
ORDER BY ingresos DESC;

-- ----------------------------------------------------------------------------
-- CONSULTA 13 [COMPLEJA]: Días de stock y acción recomendada
-- Negocio: Reabastecimiento: qué pedir ya y qué solo monitorear.
-- Técnica: JOIN + CASE + división calculada (los días NO se almacenan)
-- ----------------------------------------------------------------------------
SELECT p.nombre                                          AS producto,
       s.nombre                                          AS sede,
       i.cantidadDisponible                              AS inventario,
       i.demandaDiaria                                   AS demanda_diaria,
       ROUND(i.cantidadDisponible / i.demandaDiaria, 1)  AS dias_stock,
       CASE
         WHEN i.cantidadDisponible = 0 THEN 'AGOTADO'
         WHEN i.cantidadDisponible / i.demandaDiaria < 5  THEN 'CRITICO'
         WHEN i.cantidadDisponible / i.demandaDiaria <= 15 THEN 'ALERTA'
         ELSE 'SEGURO'
       END                                               AS categoria_estado,
       CASE
         WHEN i.cantidadDisponible = 0 THEN 'Pedido inmediato'
         WHEN i.cantidadDisponible / i.demandaDiaria < 5  THEN 'Pedido de emergencia'
         WHEN i.cantidadDisponible / i.demandaDiaria <= 15 THEN 'Realizar pedido normal'
         ELSE 'Mantener monitoreo'
       END                                               AS accion_recomendada
FROM INVENTARIO i
JOIN PRODUCTO p ON p.idProducto = i.idProducto
JOIN SEDE     s ON s.idSede     = i.idSede
WHERE p.activo = TRUE
ORDER BY dias_stock ASC
LIMIT 25;

-- ----------------------------------------------------------------------------
-- CONSULTA 14 [COMPLEJA]: Clientes que gastan por encima del promedio
-- Negocio: Segmento de alto valor para campañas de fidelización.
-- Técnica: Subconsulta escalar en el HAVING + LEFT JOIN
-- ----------------------------------------------------------------------------
SELECT cl.nombres || ' ' || cl.apellidos AS cliente,
       cl.tipoCliente                    AS tipo,
       cl.ciudad,
       COUNT(o.idOrden)                  AS compras,
       SUM(o.total)                      AS total_gastado,
       t.puntosAcumulados                AS puntos_tarjeta
FROM CLIENTE cl
JOIN ORDEN o                 ON o.idCliente = cl.idCliente AND o.estado = 'PAGADA'
LEFT JOIN TARJETA_AMARILLA t ON t.idCliente = cl.idCliente
GROUP BY cl.idCliente, cl.nombres, cl.apellidos, cl.tipoCliente, cl.ciudad,
         t.puntosAcumulados
HAVING SUM(o.total) > (
    SELECT AVG(total_cliente)
    FROM (SELECT SUM(total) AS total_cliente
          FROM ORDEN WHERE estado = 'PAGADA'
          GROUP BY idCliente) AS gasto_por_cliente
)
ORDER BY total_gastado DESC
LIMIT 15;

-- ----------------------------------------------------------------------------
-- CONSULTA 15 [COMPLEJA]: Margen bruto: precio de venta contra costo de compra
-- Negocio: Rentabilidad real por producto.
-- Técnica: JOIN entre el lado de ventas y el de compras + AVG
-- ----------------------------------------------------------------------------
SELECT p.nombre                                              AS producto,
       c.nombre                                              AS categoria,
       p.precioVenta                                         AS precio_venta,
       ROUND(AVG(dc.precioUnitario), 0)                      AS costo_promedio,
       ROUND(p.precioVenta - AVG(dc.precioUnitario), 0)      AS margen_unitario,
       ROUND(100.0 * (p.precioVenta - AVG(dc.precioUnitario))
             / p.precioVenta, 2)                             AS margen_pct
FROM PRODUCTO p
JOIN CATEGORIA c       ON c.idCategoria = p.idCategoria
JOIN DETALLE_COMPRA dc ON dc.idProducto = p.idProducto
GROUP BY p.idProducto, p.nombre, c.nombre, p.precioVenta
ORDER BY margen_pct DESC
LIMIT 15;

-- ----------------------------------------------------------------------------
-- CONSULTA 16 [COMPLEJA]: Marca propia (Doña Lupe) frente a marcas de terceros
-- Negocio: Peso real de la marca blanca en la facturación de la cadena.
-- Técnica: CASE + GROUP BY sobre booleano + ventana
-- ----------------------------------------------------------------------------
SELECT CASE WHEN m.esMarcaPropia THEN 'Marca propia (Doña Lupe)'
            ELSE 'Marca de terceros' END                             AS tipo_marca,
       COUNT(DISTINCT p.idProducto)                                  AS referencias,
       SUM(d.cantidad)                                               AS unidades,
       SUM(d.subtotal)                                               AS ingresos,
       ROUND(100.0 * SUM(d.subtotal) / SUM(SUM(d.subtotal)) OVER (), 2) AS participacion_pct
FROM DETALLE_ORDEN d
JOIN PRODUCTO p ON p.idProducto = d.idProducto
JOIN MARCA    m ON m.idMarca    = p.idMarca
JOIN ORDEN    o ON o.idOrden    = d.idOrden
WHERE o.estado = 'PAGADA'
GROUP BY m.esMarcaPropia
ORDER BY ingresos DESC;

-- ----------------------------------------------------------------------------
-- CONSULTA 17 [COMPLEJA]: Ranking de productos dentro de cada categoría
-- Negocio: El más vendido de cada línea (para destacarlo en el punto de venta).
-- Técnica: Subconsulta con RANK() OVER (PARTITION BY ...)
-- ----------------------------------------------------------------------------
SELECT categoria, producto, unidades, ingresos
FROM (
    SELECT c.nombre         AS categoria,
           p.nombre         AS producto,
           SUM(d.cantidad)  AS unidades,
           SUM(d.subtotal)  AS ingresos,
           RANK() OVER (PARTITION BY c.idCategoria
                        ORDER BY SUM(d.cantidad) DESC) AS puesto
    FROM DETALLE_ORDEN d
    JOIN PRODUCTO  p ON p.idProducto  = d.idProducto
    JOIN CATEGORIA c ON c.idCategoria = p.idCategoria
    JOIN ORDEN     o ON o.idOrden     = d.idOrden
    WHERE o.estado = 'PAGADA'
    GROUP BY c.idCategoria, c.nombre, p.idProducto, p.nombre
) AS ranking
WHERE puesto = 1
ORDER BY ingresos DESC;

-- ----------------------------------------------------------------------------
-- CONSULTA 18 [COMPLEJA]: Desempeño de proveedores: calificación contra entregas reales
-- Negocio: ¿La calificación que les damos coincide con lo que realmente entregan?
-- Técnica: JOIN + GROUP BY + COUNT FILTER + porcentaje de cumplimiento
-- ----------------------------------------------------------------------------
SELECT pr.razonSocial                                        AS proveedor,
       pr.calificacion,
       pr.tiempoEntregaPromedio                              AS dias_entrega,
       pr.condicionesPago                                    AS dias_pago,
       COUNT(co.idCompra)                                    AS pedidos,
       COUNT(*) FILTER (WHERE co.estado = 'RECIBIDA')        AS recibidos,
       COUNT(*) FILTER (WHERE co.estado = 'CANCELADA')       AS cancelados,
       ROUND(100.0 * COUNT(*) FILTER (WHERE co.estado = 'RECIBIDA')
             / NULLIF(COUNT(co.idCompra), 0), 1)             AS cumplimiento_pct,
       SUM(co.total)                                         AS monto_comprado
FROM PROVEEDOR pr
JOIN COMPRA co ON co.idProveedor = pr.idProveedor
GROUP BY pr.idProveedor, pr.razonSocial, pr.calificacion,
         pr.tiempoEntregaPromedio, pr.condicionesPago
ORDER BY monto_comprado DESC
LIMIT 15;

-- ----------------------------------------------------------------------------
-- CONSULTA 19 [COMPLEJA]: Productos nunca vendidos (inventario inmovilizado)
-- Negocio: Candidatos a promoción, descuento o descontinuación.
-- Técnica: Subconsulta NOT EXISTS + JOIN con inventario
-- ----------------------------------------------------------------------------
SELECT p.nombre                     AS producto,
       c.nombre                     AS categoria,
       pr.razonSocial               AS proveedor,
       p.precioVenta                AS precio,
       COALESCE(SUM(i.cantidadDisponible), 0) AS unidades_en_bodega,
       ROUND(COALESCE(SUM(i.cantidadDisponible), 0) * p.precioVenta, 0)
                                    AS capital_inmovilizado
FROM PRODUCTO p
JOIN CATEGORIA c       ON c.idCategoria  = p.idCategoria
JOIN PROVEEDOR pr      ON pr.idProveedor = p.idProveedor
LEFT JOIN INVENTARIO i ON i.idProducto   = p.idProducto
WHERE NOT EXISTS (
    SELECT 1
    FROM DETALLE_ORDEN d
    JOIN ORDEN o ON o.idOrden = d.idOrden AND o.estado = 'PAGADA'
    WHERE d.idProducto = p.idProducto
)
GROUP BY p.idProducto, p.nombre, c.nombre, pr.razonSocial, p.precioVenta
ORDER BY capital_inmovilizado DESC
LIMIT 20;

-- ----------------------------------------------------------------------------
-- CONSULTA 20 [COMPLEJA]: Productividad de empleados frente al promedio de su sede
-- Negocio: Comisiones justas: comparar a cada cajero con su propia tienda.
-- Técnica: Función de ventana con PARTITION BY + comparación contra el promedio
-- ----------------------------------------------------------------------------
SELECT empleado, cargo, sede, ventas, monto_vendido,
       promedio_sede,
       ROUND(100.0 * monto_vendido / NULLIF(promedio_sede, 0) - 100, 1)
           AS diferencia_pct
FROM (
    SELECT e.nombres || ' ' || e.apellidos                       AS empleado,
           e.cargo,
           s.nombre                                              AS sede,
           COUNT(o.idOrden)                                      AS ventas,
           SUM(o.total)                                          AS monto_vendido,
           ROUND(AVG(SUM(o.total)) OVER (PARTITION BY s.idSede), 0)
                                                                 AS promedio_sede
    FROM EMPLEADO e
    JOIN SEDE  s ON s.idSede = e.idSede
    JOIN ORDEN o ON o.idEmpleado = e.idEmpleado AND o.estado = 'PAGADA'
    GROUP BY e.idEmpleado, e.nombres, e.apellidos, e.cargo, s.idSede, s.nombre
) AS desempeno
ORDER BY diferencia_pct DESC
LIMIT 15;

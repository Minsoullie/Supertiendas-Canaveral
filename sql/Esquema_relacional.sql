SET client_encoding = 'UTF8';

BEGIN;



--  BLOQUE 1 — ENTIDADES INDEPENDIENTES (no tienen llaves foráneas)


-- EMPRESA
-- Datos del vendedor que deben aparecer en la Factura Electrónica de Venta
-- (NIT, razón social y dirección), según la normativa de la DIAN.

CREATE TABLE EMPRESA (
    idEmpresa        SERIAL          NOT NULL,
    nit              VARCHAR(20)     NOT NULL,
    razonSocial      VARCHAR(150)    NOT NULL,
    direccion        VARCHAR(200)    NOT NULL,
    ciudad           VARCHAR(80)     NOT NULL,
    telefono         VARCHAR(20)     NOT NULL,
    email            VARCHAR(120)    NOT NULL,
    sitioWeb         VARCHAR(120)    NOT NULL DEFAULT '',
    CONSTRAINT pk_empresa   PRIMARY KEY (idEmpresa),
    CONSTRAINT uq_emp_nit   UNIQUE (nit)
);


-- RESOLUCION_DIAN
-- Resolución de facturación electrónica autorizada por la DIAN. La numeración
-- de las facturas (prefijo + consecutivo) debe caer dentro de su rango y de su
-- período de vigencia.

CREATE TABLE RESOLUCION_DIAN (
    idResolucion     SERIAL          NOT NULL,
    numeroResolucion VARCHAR(30)     NOT NULL,
    prefijo          VARCHAR(10)     NOT NULL,
    rangoDesde       INTEGER         NOT NULL,
    rangoHasta       INTEGER         NOT NULL,
    vigenciaDesde    DATE            NOT NULL,
    vigenciaHasta    DATE            NOT NULL,
    CONSTRAINT pk_resolucion  PRIMARY KEY (idResolucion),
    CONSTRAINT uq_res_numero  UNIQUE (numeroResolucion),
    CONSTRAINT chk_res_rango     CHECK (rangoHasta > rangoDesde),
    CONSTRAINT chk_res_vigencia  CHECK (vigenciaHasta > vigenciaDesde)
);


-- Persona natural o jurídica que compra en la cadena.
--   * habeasData: autorización del tratamiento de datos (Ley 1581 de 2012).
--   * Se guardan dos direcciones: la de residencia y la operativa (empresas).
--   * Una persona JURIDICA se identifica obligatoriamente con NIT.

CREATE TABLE CLIENTE (
    idCliente            SERIAL          NOT NULL,
    tipoDocumento        VARCHAR(20)     NOT NULL,
    numeroDocumento      VARCHAR(20)     NOT NULL,
    nombres              VARCHAR(80)     NOT NULL,
    apellidos            VARCHAR(80)     NOT NULL,
    tipoCliente          VARCHAR(20)     NOT NULL,
    regimenTributario    VARCHAR(20)     NOT NULL DEFAULT 'NO_RESPONSABLE',
    representanteLegal   VARCHAR(120)    NOT NULL,
    habeasData           BOOLEAN         NOT NULL DEFAULT FALSE,
    email                VARCHAR(120)    NOT NULL,
    telefono             VARCHAR(20)     NOT NULL,
    ciudad               VARCHAR(80)     NOT NULL,
    direccionResidencia  VARCHAR(200)    NOT NULL,
    direccionOperativa   VARCHAR(200),
    fechaRegistro        DATE            NOT NULL DEFAULT CURRENT_DATE,
    CONSTRAINT pk_cliente        PRIMARY KEY (idCliente),
    CONSTRAINT uq_cli_documento  UNIQUE (numeroDocumento),
    CONSTRAINT uq_cli_email      UNIQUE (email),
    CONSTRAINT chk_cli_tipodoc      CHECK (tipoDocumento IN ('CC','CE','NIT','PP','TI')),
    CONSTRAINT chk_cli_tipocliente  CHECK (tipoCliente IN ('NATURAL','JURIDICO')),
    CONSTRAINT chk_cli_regimen      CHECK (regimenTributario IN ('RESPONSABLE','NO_RESPONSABLE')),
    -- Regla de negocio: toda persona jurídica se identifica con NIT
    CONSTRAINT chk_cli_juridico_nit CHECK (NOT (tipoCliente = 'JURIDICO') OR tipoDocumento = 'NIT')
);

-- -----------------------------------------------------------------------------
-- SEDE
-- Las 16 tiendas de la cadena en el Valle del Cauca.
-- -----------------------------------------------------------------------------
CREATE TABLE SEDE (
    idSede           SERIAL          NOT NULL,
    nombre           VARCHAR(100)    NOT NULL,
    direccion        VARCHAR(200)    NOT NULL,
    ciudad           VARCHAR(80)     NOT NULL,
    departamento     VARCHAR(80)     NOT NULL,
    telefono         VARCHAR(20)     NOT NULL,
    horarioApertura  TIME            NOT NULL,
    horarioCierre    TIME            NOT NULL,
    CONSTRAINT pk_sede          PRIMARY KEY (idSede),
    CONSTRAINT uq_sede_nombre   UNIQUE (nombre),
    CONSTRAINT chk_sede_horario CHECK (horarioCierre > horarioApertura)
);

-- -----------------------------------------------------------------------------
-- CATEGORIA
-- Clasificación del catálogo (tabla de consulta / lookup).
-- Se extrae de PRODUCTO para eliminar la dependencia transitiva (3FN).
-- -----------------------------------------------------------------------------
CREATE TABLE CATEGORIA (
    idCategoria      SERIAL          NOT NULL,
    nombre           VARCHAR(80)     NOT NULL,
    descripcion      TEXT,
    CONSTRAINT pk_categoria    PRIMARY KEY (idCategoria),
    CONSTRAINT uq_cat_nombre   UNIQUE (nombre)
);

-- -----------------------------------------------------------------------------
-- MARCA
-- Marcas de los productos. `esMarcaPropia` identifica la marca blanca de la
-- cadena (Doña Lupe).
-- -----------------------------------------------------------------------------
CREATE TABLE MARCA (
    idMarca          SERIAL          NOT NULL,
    nombre           VARCHAR(80)     NOT NULL,
    esMarcaPropia    BOOLEAN         NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_marca         PRIMARY KEY (idMarca),
    CONSTRAINT uq_marca_nombre  UNIQUE (nombre)
);

-- -----------------------------------------------------------------------------
-- PROVEEDOR
-- Incluye la información tributaria (RUT, régimen), la certificación bancaria
-- necesaria para programar pagos, las condiciones comerciales y los tres
-- contactos que exige la operación (comercial, cartera y logístico).
-- -----------------------------------------------------------------------------
CREATE TABLE PROVEEDOR (
    idProveedor            SERIAL          NOT NULL,
    tipoDocumento          VARCHAR(20)     NOT NULL DEFAULT 'NIT',
    nit                    VARCHAR(20)     NOT NULL,
    razonSocial            VARCHAR(150)    NOT NULL,
    rut                    VARCHAR(30)     NOT NULL,
    regimenTributario      VARCHAR(20)     NOT NULL DEFAULT 'RESPONSABLE',
    representanteLegal     VARCHAR(120)    NOT NULL,
    habeasData             BOOLEAN         NOT NULL DEFAULT TRUE,
    ciudad                 VARCHAR(80)     NOT NULL,
    direccion              VARCHAR(200)    NOT NULL,
    telefono               VARCHAR(20)     NOT NULL,
    email                  VARCHAR(120)    NOT NULL,
    -- Certificación bancaria (indispensable para pagar por transferencia)
    banco                  VARCHAR(60)     NOT NULL,
    tipoCuenta             VARCHAR(15)     NOT NULL DEFAULT 'CORRIENTE',
    numeroCuenta           VARCHAR(30)     NOT NULL,
    -- Condiciones comerciales
    tipoProveedor          VARCHAR(25)     NOT NULL,
    tiempoEntregaPromedio  INTEGER         NOT NULL DEFAULT 7,   -- en días
    condicionesPago        INTEGER         NOT NULL DEFAULT 30,  -- en días
    calificacion           INTEGER         NOT NULL DEFAULT 3,   -- escala de 1 a 5
    -- Contactos
    contactoComercial      VARCHAR(120)    NOT NULL,
    contactoCartera        VARCHAR(120)    NOT NULL,
    contactoLogistico      VARCHAR(120)    NOT NULL,
    CONSTRAINT pk_proveedor    PRIMARY KEY (idProveedor),
    CONSTRAINT uq_prov_nit     UNIQUE (nit),
    CONSTRAINT uq_prov_email   UNIQUE (email),
    CONSTRAINT chk_prov_calificacion CHECK (calificacion BETWEEN 1 AND 5),
    CONSTRAINT chk_prov_entrega      CHECK (tiempoEntregaPromedio > 0),
    CONSTRAINT chk_prov_pago         CHECK (condicionesPago >= 0),
    CONSTRAINT chk_prov_tipocuenta   CHECK (tipoCuenta IN ('AHORROS','CORRIENTE'))
);

-- -----------------------------------------------------------------------------
-- METODO_PAGO
-- Medios de pago aceptados (efectivo, tarjetas, PSE, Nequi, Daviplata, bonos).
-- -----------------------------------------------------------------------------
CREATE TABLE METODO_PAGO (
    idMetodoPago     SERIAL          NOT NULL,
    nombre           VARCHAR(60)     NOT NULL,
    descripcion      TEXT,
    CONSTRAINT pk_metodo_pago  PRIMARY KEY (idMetodoPago),
    CONSTRAINT uq_mp_nombre    UNIQUE (nombre)
);


-- #############################################################################
--  BLOQUE 2 — ENTIDADES DEPENDIENTES
-- #############################################################################

-- -----------------------------------------------------------------------------
-- TARJETA_AMARILLA  (1:N desde CLIENTE)
-- Programa de fidelización. Si se elimina el cliente, su tarjeta desaparece
-- con él: ON DELETE CASCADE.
-- -----------------------------------------------------------------------------
CREATE TABLE TARJETA_AMARILLA (
    idTarjeta        SERIAL          NOT NULL,
    idCliente        INTEGER         NOT NULL,
    numeroTarjeta    VARCHAR(20)     NOT NULL,
    fechaEmision     DATE            NOT NULL DEFAULT CURRENT_DATE,
    puntosAcumulados INTEGER         NOT NULL DEFAULT 0,
    estado           VARCHAR(15)     NOT NULL DEFAULT 'ACTIVA',
    CONSTRAINT pk_tarjeta      PRIMARY KEY (idTarjeta),
    CONSTRAINT fk_tar_cliente  FOREIGN KEY (idCliente)
        REFERENCES CLIENTE (idCliente) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_tar_numero   UNIQUE (numeroTarjeta),
    CONSTRAINT chk_tar_puntos  CHECK (puntosAcumulados >= 0),
    CONSTRAINT chk_tar_estado  CHECK (estado IN ('ACTIVA','INACTIVA','BLOQUEADA'))
);

-- -----------------------------------------------------------------------------
-- EMPLEADO  (1:N desde SEDE)
-- ON DELETE RESTRICT: no se puede borrar una sede que todavía tiene personal.
-- -----------------------------------------------------------------------------
CREATE TABLE EMPLEADO (
    idEmpleado       SERIAL          NOT NULL,
    idSede           INTEGER         NOT NULL,
    numeroDocumento  VARCHAR(20)     NOT NULL,
    nombres          VARCHAR(80)     NOT NULL,
    apellidos        VARCHAR(80)     NOT NULL,
    cargo            VARCHAR(60)     NOT NULL,
    salario          NUMERIC(12,2)   NOT NULL,
    fechaIngreso     DATE            NOT NULL DEFAULT CURRENT_DATE,
    CONSTRAINT pk_empleado       PRIMARY KEY (idEmpleado),
    CONSTRAINT fk_emp_sede       FOREIGN KEY (idSede)
        REFERENCES SEDE (idSede) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_emp_documento  UNIQUE (numeroDocumento),
    CONSTRAINT chk_emp_salario   CHECK (salario > 0)
);

-- -----------------------------------------------------------------------------
-- PRODUCTO  (1:N desde CATEGORIA, MARCA y PROVEEDOR)
--
--   * idProveedor es OBLIGATORIO: no se puede registrar un producto o insumo
--     de un proveedor que no exista previamente (regla del negocio).
--   * `activo` implementa la ELIMINACIÓN LÓGICA: el registro nunca se borra
--     físicamente, para no perder el histórico de movimientos de inventario.
--   * El IVA sigue las cuatro categorías de la legislación colombiana. Los
--     productos EXCLUIDOS no causan el impuesto (el sistema no calcula nada);
--     los EXENTOS sí lo causan, pero con tarifa 0%.
--   * Los "días de stock" NO se almacenan aquí (ni en ninguna tabla): son un
--     dato derivado que se calcula en la vista vw_dias_stock.
-- -----------------------------------------------------------------------------
CREATE TABLE PRODUCTO (
    idProducto       SERIAL          NOT NULL,
    idCategoria      INTEGER         NOT NULL,
    idMarca          INTEGER         NOT NULL,
    idProveedor      INTEGER         NOT NULL,
    codigoBarras     VARCHAR(30)     NOT NULL,
    nombre           VARCHAR(150)    NOT NULL,
    descripcion      TEXT,
    precioVenta      NUMERIC(12,2)   NOT NULL,
    unidadMedida     VARCHAR(20)     NOT NULL,
    categoriaIva     VARCHAR(15)     NOT NULL DEFAULT 'GENERAL',
    iva              NUMERIC(5,2)    NOT NULL DEFAULT 19,
    activo           BOOLEAN         NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_producto        PRIMARY KEY (idProducto),
    CONSTRAINT fk_prod_categoria  FOREIGN KEY (idCategoria)
        REFERENCES CATEGORIA (idCategoria) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_prod_marca      FOREIGN KEY (idMarca)
        REFERENCES MARCA (idMarca) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_prod_proveedor  FOREIGN KEY (idProveedor)
        REFERENCES PROVEEDOR (idProveedor) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_prod_barras     UNIQUE (codigoBarras),
    CONSTRAINT chk_prod_precio    CHECK (precioVenta > 0),
    CONSTRAINT chk_prod_unidad    CHECK (unidadMedida IN ('UND','KG','LT','MT','GR','ML')),
    CONSTRAINT chk_prod_iva       CHECK (iva IN (0, 5, 19)),
    -- La tarifa debe ser coherente con la categoría de IVA declarada
    CONSTRAINT chk_prod_iva_categoria CHECK (
           (categoriaIva = 'GENERAL'     AND iva = 19)
        OR (categoriaIva = 'DIFERENCIAL' AND iva = 5)
        OR (categoriaIva = 'EXENTO'      AND iva = 0)
        OR (categoriaIva = 'EXCLUIDO'    AND iva = 0)
    )
);

-- -----------------------------------------------------------------------------
-- INVENTARIO  (relación N:M entre PRODUCTO y SEDE, con atributos)
--
--   * Un producto solo puede tener UNA fila de inventario por sede.
--   * demandaDiaria permite calcular los días de stock:
--         dias_stock = cantidadDisponible / demandaDiaria
--     Ese valor NO se almacena: se calcula (ver vw_dias_stock).
-- -----------------------------------------------------------------------------
CREATE TABLE INVENTARIO (
    idInventario        SERIAL       NOT NULL,
    idProducto          INTEGER      NOT NULL,
    idSede              INTEGER      NOT NULL,
    cantidadDisponible  INTEGER      NOT NULL DEFAULT 0,
    demandaDiaria       NUMERIC(10,2) NOT NULL DEFAULT 1.00,
    stockMinimo         INTEGER      NOT NULL DEFAULT 5,
    fechaActualizacion  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_inventario      PRIMARY KEY (idInventario),
    CONSTRAINT fk_inv_producto    FOREIGN KEY (idProducto)
        REFERENCES PRODUCTO (idProducto) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_inv_sede        FOREIGN KEY (idSede)
        REFERENCES SEDE (idSede) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_inv_prod_sede   UNIQUE (idProducto, idSede),
    CONSTRAINT chk_inv_cantidad   CHECK (cantidadDisponible >= 0),
    CONSTRAINT chk_inv_stock_min  CHECK (stockMinimo >= 0),
    CONSTRAINT chk_inv_demanda    CHECK (demandaDiaria > 0)
);

-- -----------------------------------------------------------------------------
-- ORDEN  (Factura Electrónica de Venta)
--
--   * La numeración es la autorizada por la DIAN: prefijo + consecutivo, dentro
--     del rango de una resolución vigente.
--   * Se registran las dos fechas que exige la norma: generación y expedición.
--   * subtotal / iva / total son "snapshots" del momento de la venta. La regla
--     total = subtotal + iva se garantiza con una restricción CHECK.
--   * Una factura guardada NO se edita ni se elimina: solo se ANULA (cambio de
--     estado), para que el rastro contable quede inalterable.
-- -----------------------------------------------------------------------------
CREATE TABLE ORDEN (
    idOrden          SERIAL          NOT NULL,
    idResolucion     INTEGER         NOT NULL,
    prefijo          VARCHAR(10)     NOT NULL,
    numeroFactura    INTEGER         NOT NULL,
    idCliente        INTEGER         NOT NULL,
    idEmpleado       INTEGER         NOT NULL,
    idSede           INTEGER         NOT NULL,
    idMetodoPago     INTEGER         NOT NULL,
    fechaOrden       TIMESTAMP       NOT NULL,
    fechaExpedicion  TIMESTAMP,
    subtotal         NUMERIC(14,2)   NOT NULL,
    iva              NUMERIC(14,2)   NOT NULL DEFAULT 0,
    total            NUMERIC(14,2)   NOT NULL,
    tipoVenta        VARCHAR(20)     NOT NULL DEFAULT 'PRESENCIAL',
    estado           VARCHAR(20)     NOT NULL DEFAULT 'PENDIENTE',
    cufe             VARCHAR(96),
    CONSTRAINT pk_orden           PRIMARY KEY (idOrden),
    CONSTRAINT fk_ord_resolucion  FOREIGN KEY (idResolucion)
        REFERENCES RESOLUCION_DIAN (idResolucion) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_ord_cliente     FOREIGN KEY (idCliente)
        REFERENCES CLIENTE (idCliente) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_ord_empleado    FOREIGN KEY (idEmpleado)
        REFERENCES EMPLEADO (idEmpleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_ord_sede        FOREIGN KEY (idSede)
        REFERENCES SEDE (idSede) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_ord_metodopago  FOREIGN KEY (idMetodoPago)
        REFERENCES METODO_PAGO (idMetodoPago) ON DELETE RESTRICT ON UPDATE CASCADE,
    -- El consecutivo no se puede repetir dentro de un mismo prefijo
    CONSTRAINT uq_ord_factura     UNIQUE (prefijo, numeroFactura),
    CONSTRAINT chk_ord_tipo       CHECK (tipoVenta IN ('PRESENCIAL','ONLINE')),
    CONSTRAINT chk_ord_estado     CHECK (estado IN ('PENDIENTE','PAGADA','ANULADA')),
    CONSTRAINT chk_ord_valores    CHECK (subtotal >= 0 AND iva >= 0),
    CONSTRAINT chk_ord_total      CHECK (total = subtotal + iva)
);

-- -----------------------------------------------------------------------------
-- COMPRA  (Orden de Pedido a un proveedor)
--
--   * No se puede crear sin un proveedor previamente registrado (FK obligatoria).
--   * El estado inicia SIEMPRE en PENDIENTE.
--   * Al pasar a RECIBIDA, el trigger trg_compra_recibida suma automáticamente
--     las unidades al inventario de la sede (ver 04_vistas_y_triggers.sql).
-- -----------------------------------------------------------------------------
CREATE TABLE COMPRA (
    idCompra         SERIAL          NOT NULL,
    idProveedor      INTEGER         NOT NULL,
    idSede           INTEGER         NOT NULL,
    fechaCompra      DATE            NOT NULL DEFAULT CURRENT_DATE,
    lugarEntrega     VARCHAR(150)    NOT NULL,
    total            NUMERIC(14,2)   NOT NULL DEFAULT 0,
    estado           VARCHAR(20)     NOT NULL DEFAULT 'PENDIENTE',
    CONSTRAINT pk_compra          PRIMARY KEY (idCompra),
    CONSTRAINT fk_comp_proveedor  FOREIGN KEY (idProveedor)
        REFERENCES PROVEEDOR (idProveedor) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_comp_sede       FOREIGN KEY (idSede)
        REFERENCES SEDE (idSede) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_comp_total     CHECK (total >= 0),
    CONSTRAINT chk_comp_estado    CHECK (estado IN ('PENDIENTE','RECIBIDA','CANCELADA'))
);

-- -----------------------------------------------------------------------------
-- DETALLE_ORDEN  (resuelve la relación N:M entre ORDEN y PRODUCTO)
--
--   * El IVA se discrimina POR CADA ÍTEM (exigencia de la factura electrónica),
--     no solo en el total de la factura.
--   * Si se elimina la factura, sus líneas se van con ella: ON DELETE CASCADE.
--   * Un producto no se puede repetir dentro de la misma factura (se sube la
--     cantidad en su lugar).
-- -----------------------------------------------------------------------------
CREATE TABLE DETALLE_ORDEN (
    idDetalleOrden   SERIAL          NOT NULL,
    idOrden          INTEGER         NOT NULL,
    idProducto       INTEGER         NOT NULL,
    cantidad         INTEGER         NOT NULL,
    precioUnitario   NUMERIC(12,2)   NOT NULL,
    subtotal         NUMERIC(14,2)   NOT NULL,
    ivaPorcentaje    NUMERIC(5,2)    NOT NULL DEFAULT 0,
    ivaValor         NUMERIC(14,2)   NOT NULL DEFAULT 0,
    CONSTRAINT pk_detalle_orden     PRIMARY KEY (idDetalleOrden),
    CONSTRAINT fk_dord_orden        FOREIGN KEY (idOrden)
        REFERENCES ORDEN (idOrden) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_dord_producto     FOREIGN KEY (idProducto)
        REFERENCES PRODUCTO (idProducto) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_dord_prod_orden   UNIQUE (idOrden, idProducto),
    CONSTRAINT chk_dord_cantidad    CHECK (cantidad > 0),
    CONSTRAINT chk_dord_precio      CHECK (precioUnitario > 0),
    CONSTRAINT chk_dord_subtotal    CHECK (subtotal = precioUnitario * cantidad)
);

-- -----------------------------------------------------------------------------
-- DETALLE_COMPRA  (resuelve la relación N:M entre COMPRA y PRODUCTO)
--
--   * Regla del negocio: la cantidad de un ítem va de 1 a 500 unidades.
-- -----------------------------------------------------------------------------
CREATE TABLE DETALLE_COMPRA (
    idDetalleCompra  SERIAL          NOT NULL,
    idCompra         INTEGER         NOT NULL,
    idProducto       INTEGER         NOT NULL,
    cantidad         INTEGER         NOT NULL,
    precioUnitario   NUMERIC(12,2)   NOT NULL,
    CONSTRAINT pk_detalle_compra    PRIMARY KEY (idDetalleCompra),
    CONSTRAINT fk_dcomp_compra      FOREIGN KEY (idCompra)
        REFERENCES COMPRA (idCompra) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_dcomp_producto    FOREIGN KEY (idProducto)
        REFERENCES PRODUCTO (idProducto) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_dcomp_prod_comp   UNIQUE (idCompra, idProducto),
    CONSTRAINT chk_dcomp_cantidad   CHECK (cantidad BETWEEN 1 AND 500),
    CONSTRAINT chk_dcomp_precio     CHECK (precioUnitario > 0)
);


-- #############################################################################
--  BLOQUE 3 — ÍNDICES
--  Sobre las columnas por las que más se filtra y se hacen JOIN.
-- #############################################################################

-- Búsqueda de clientes por documento (la más frecuente en caja)
CREATE INDEX idx_cliente_documento     ON CLIENTE (numeroDocumento);

-- Catálogo: filtros por categoría, proveedor y búsqueda por nombre
CREATE INDEX idx_producto_categoria    ON PRODUCTO (idCategoria);
CREATE INDEX idx_producto_proveedor    ON PRODUCTO (idProveedor);
CREATE INDEX idx_producto_nombre       ON PRODUCTO (nombre);

-- Inventario por tienda
CREATE INDEX idx_inventario_sede       ON INVENTARIO (idSede);

-- Reportes de ventas: por fecha, sede, cliente y estado
CREATE INDEX idx_orden_fecha           ON ORDEN (fechaOrden);
CREATE INDEX idx_orden_sede            ON ORDEN (idSede);
CREATE INDEX idx_orden_cliente         ON ORDEN (idCliente);
CREATE INDEX idx_orden_estado          ON ORDEN (estado);

-- Productos más vendidos
CREATE INDEX idx_detalleorden_producto ON DETALLE_ORDEN (idProducto);

-- Compras por proveedor
CREATE INDEX idx_compra_proveedor      ON COMPRA (idProveedor);


COMMIT;

-- =============================================================================
--  FIN DEL ESQUEMA RELACIONAL
--
--  Resumen (verificado contra la base de datos ya creada):
--     16 tablas · 16 llaves primarias · 18 llaves foráneas
--     17 restricciones UNIQUE · 32 restricciones CHECK · 11 índices
--     ---------------------------------------------------------------
--     83 restricciones en total
--
--  Siguiente paso: cargar los datos con 02_datos_supertiendas_canaveral.sql
--  y crear las vistas y los triggers con 04_vistas_y_triggers.sql
-- =============================================================================

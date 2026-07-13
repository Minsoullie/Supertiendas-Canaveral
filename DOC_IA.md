# DOC_IA.md — Documentación del uso de Inteligencia Artificial Generativa

Este documento cumple el **Requisito de Documentación Obligatoria** del enunciado del
proyecto. Registra, para cada uso de IA: el **prompt utilizado**, el **resultado obtenido**
y el **ajuste manual** que hubo que hacer para que el código funcionara en nuestro entorno.

| Dato | Valor |
|---|---|
| **Herramienta** | Claude (Anthropic) |
| **Modelo** | Claude Opus 4.8 |
| **Interfaz** | claude.ai (chat web) |
| **Áreas de uso** | Generación de datos sintéticos · Optimización SQL · Desarrollo web (Django) |

---

## 1. Generación de datos sintéticos

### Prompt utilizado
> «Este es el código DDL de la base de datos que estoy haciendo de la empresa Supertiendas
> Cañaveral, necesito que me ayudes con la generación de datos sintéticos, si necesitas
> información adicional coméntame.»
>
> Complementado con: *formato INSERT SQL directo · mínimo 1.000 registros de transacciones ·
> prioridad en realismo de nombres, cédulas y NIT colombianos.*

### Resultado obtenido
Un script en Python que produce un archivo `.sql` con sentencias `INSERT`, respetando el
orden de las llaves foráneas y todas las restricciones `CHECK` / `UNIQUE`. Incluyó:

* Listas de nombres y apellidos frecuentes en Colombia.
* **Dígito de verificación del NIT** calculado con el algoritmo oficial de la DIAN
  (pesos por posición, módulo 11).
* Sesgos estadísticos: popularidad desigual de productos, estacionalidad, predominio de
  ventas presenciales, etc.

### Ajuste manual
1. **Empresa real, no ficticia.** La primera versión asumió que Supertiendas Cañaveral era
   una empresa inventada y generó sedes en ciudades donde la cadena **no** opera (Cartago,
   Yumbo, Pereira) y marcas propias inventadas. Verificamos la información pública de la
   empresa y **corregimos los datos**: sus 16 tiendas están en Cali (9) y en Palmira,
   Jamundí, Candelaria, Buga, Tuluá, Zarzal y Roldanillo; su marca propia real es
   **Doña Lupe**.
2. **IVA de cuatro categorías.** El script original solo manejaba tarifas 0 / 5 / 19 y
   confundía *exento* con *excluido*. Añadimos el campo `categoria_iva` y la regla de que
   los productos **EXCLUIDOS no causan impuesto** (el sistema no calcula nada), como pide
   la legislación colombiana.
3. **`Decimal` en lugar de `float`.** Con punto flotante se perdían centavos y fallaba la
   restricción `CHECK (total = subtotal + iva)`. Se cambió todo el cálculo monetario a
   `Decimal` con `ROUND_HALF_UP`.
4. **Coherencia de negocio.** Forzamos que el empleado que atiende una factura pertenezca a
   la sede de esa factura, y que una orden de pedido solo contenga productos de su propio
   proveedor.
5. Se convirtió el script suelto en un **comando de Django** (`manage.py generar_datos`) con
   `--limpiar`, `--seed` y volúmenes parametrizables.

---

## 2. Consultas SQL

### Prompt utilizado
> «Consultas de validación: 10 consultas SELECT complejas (usando JOIN y GROUP BY) que
> demuestren aspectos interesantes de la estructura de la base de datos. Estos aspectos
> deben basarse en la naturaleza de los negocios de la empresa, ayúdame ahora con esto.»

### Resultado obtenido
Diez consultas con `JOIN` y `GROUP BY` orientadas al negocio (ranking de sedes, productos
estrella, participación por categoría, clientes valiosos, alerta de reabastecimiento,
productividad de empleados, métodos de pago, marca propia, estacionalidad y margen bruto).

### Ajuste manual
1. **Ampliación a 20 consultas.** El enunciado de la entrega final pide 20 (10 básicas +
   10 complejas). Escribimos las 10 básicas adicionales y reclasificamos las existentes.
2. **Corrección del *fan-out* del JOIN.** Al unir `ORDEN` con `DETALLE_ORDEN`, la cabecera
   se repite una vez por cada línea; sumar `o.total` ahí contaba la misma factura varias
   veces e inflaba los ingresos. Se cambió a agregar por el grano del detalle
   (`d.subtotal`) o a usar `COUNT(DISTINCT o.idOrden)`.
3. **Filtro `estado = 'PAGADA'`** en toda consulta que suma dinero, para no contar facturas
   anuladas ni pendientes.
4. La consulta de días de stock se reescribió para que **calcule** el valor
   (`inventario / demanda_diaria`) en vez de leerlo de una columna: el enunciado prohíbe
   almacenarlo.

---

## 3. Aplicación web en Django

### Prompt utilizado
> «Añade a este proyecto de Django la base de datos Postgres y toda la generación con esos
> datos sintéticos.» Y después:
> «Haz que quede todo acomodado a como lo pide, para que sea funcional la parte de la
> interfaz y las funciones de views; te mando unas donde hay cosas de CRUD básicas, puedes
> usarlas para ayudarme con la parte gráfica y que termine de ser un mejor proyecto
> (no necesita login).»

### Resultado obtenido
* Los 16 modelos de Django mapeados 1:1 con el DDL (mismos nombres de tabla, columna y
  restricciones).
* Configuración de PostgreSQL con credenciales en `.env`.
* CRUD completo de las cinco entidades, plantillas HTML, formularios y las reglas de
  integridad (eliminación lógica, facturas inalterables, campos protegidos).
* Vistas SQL y triggers de PL/pgSQL del reto opcional.

### Ajuste manual
1. **Bug en el proyecto base.** `INSTALLED_APPS` registraba la app como `'supermecado'`
   (faltaba la **r**), lo que hacía fallar cualquier comando `manage.py` con
   `ModuleNotFoundError`. Lo corregimos.
2. **`ON DELETE` / `ON UPDATE` a nivel de motor.** Django gestiona `on_delete` en Python y
   crea las llaves foráneas **sin** esas cláusulas en la base de datos. Como el DDL del
   Avance 2/3 sí las exige, escribimos una migración con SQL explícito
   (`0002_ddl_vistas_triggers.py`) que elimina las FK autogeneradas y las recrea con los
   nombres del DDL y sus reglas.
3. **Nombres de columna en minúscula.** PostgreSQL pasa a minúsculas los identificadores sin
   comillas, así que `idCliente` del DDL es en realidad `idcliente`. Hubo que enlazar cada
   campo con `db_column` para que el esquema del ORM coincidiera exactamente con el DDL.
4. **Nombre de una llave primaria.** En el DDL, la PK de `tarjeta_amarilla` se llama
   `PK_TARJETA` (no `PK_TARJETA_AMARILLA`). La migración la nombraba mal; lo detectamos
   comparando las restricciones de ambas bases con `diff` y lo corregimos con un mapa
   explícito de nombres.
5. **El trigger interfería con la carga masiva.** Al insertar el histórico de facturas, el
   trigger `trg_venta_descuenta_stock` descontaba unidades que ya estaban contempladas en el
   inventario generado. Se desactiva temporalmente solo durante la carga inicial y se
   reactiva al terminar.
6. Se descartó el `views.py` de referencia (era de otro proyecto: usaba `@login_required`,
   QR y generación de PDF). Se conservó únicamente el **patrón**: vistas basadas en
   funciones, `forms.py`, `messages` y búsqueda con `Q`.

---

## 4. Verificación (no delegada a la IA)

Para no aceptar el código a ciegas, comprobamos por nuestra cuenta:

* **Equivalencia del esquema.** Cargamos dos bases en paralelo —una con el DDL escrito a mano
  y otra con `manage.py migrate`— y comparamos la lista completa de restricciones extraída de
  `pg_constraint` con `diff`. Resultado: idénticas.
* **Los triggers.** Marcamos una orden de pedido como `RECIBIDA` y verificamos que el stock
  subiera; creamos una factura y verificamos que el stock bajara.
* **Las reglas de negocio.** Probamos que no se pueda borrar un cliente con facturas, que el
  NIT quede bloqueado al editar, que un producto no se pueda crear sin proveedor y que una
  factura solo se pueda anular (nunca editar ni eliminar).
* **La aritmética.** Consultamos que ninguna factura viole `total = subtotal + iva`.

---

## 5. Nota sobre autoría

El uso de la IA fue **complementario**. El diseño del modelo entidad-relación, las decisiones
de normalización, la elección de la empresa y las reglas de negocio son nuestras; la IA se usó
como asistente de programación y para acelerar la generación de datos y de código repetitivo.
Todo el código entregado fue revisado, ajustado y probado por el equipo, y estamos en
capacidad de explicar y sustentar cada parte.

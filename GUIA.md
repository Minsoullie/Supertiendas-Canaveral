# Guía completa — Supertiendas Cañaveral

Guía de referencia personal: qué trae el proyecto, cómo ponerlo a funcionar de cero,
y cómo está armado el esquema de la base de datos por dentro.

---

## 1. Qué es esto, en una frase

Una app web en **Django** conectada a **PostgreSQL** que administra clientes, proveedores,
productos, inventario, facturas y órdenes de pedido de Supertiendas Cañaveral, con 16 tablas,
3 vistas, 2 triggers en PL/pgSQL, datos sintéticos y 20 consultas SQL ya escritas.

No tiene login — entras directo a la app.

---

## 2. Ponerlo a funcionar de cero (checklist)

### 2.1. Necesitas instalado
- Python 3.10 o más nuevo
- PostgreSQL (14+; se probó con la 16)

Verifica con:
```bash
python3 --version
psql --version
```

### 2.2. Descomprime el proyecto y entra a la carpeta
```bash
cd Supertiendas-Canaveral
```

### 2.3. Crea el entorno virtual e instala dependencias
```bash
python3 -m venv venv
source venv/bin/activate        # en Windows: venv\Scripts\activate
pip install -r requirements.txt
```
Esto instala: `Django`, `psycopg2-binary` (el conector a PostgreSQL) y `python-dotenv`
(para leer el archivo `.env`).

> **¿Es obligatorio el `venv`?** No, técnicamente podrías instalar las 3 librerías
> directo en tu Python del sistema (saltándote los pasos de `venv`/`activate`). Pero
> conviene igual: aísla estas dependencias para que no choquen con las de otro proyecto,
> y en Ubuntu/Debian recientes `pip` incluso **rechaza** instalar fuera de un entorno
> virtual por defecto (error *"externally-managed-environment"*). Si de verdad quieres
> saltártelo, la salida es `pip install -r requirements.txt --break-system-packages`. Y si
> algo se daña dentro del `venv`, la solución es simple: borras la carpeta `venv/` y la
> vuelves a crear.

### 2.4. Crea el usuario y la base de datos en PostgreSQL
Abre `psql` (o pgAdmin) como superusuario y corre:
```sql
CREATE ROLE canaveral_user LOGIN PASSWORD 'canaveral2025';
CREATE DATABASE canaveral_db OWNER canaveral_user;
GRANT ALL PRIVILEGES ON DATABASE canaveral_db TO canaveral_user;
```
Si ya tienes PostgreSQL con otro usuario/base, no hay problema: solo ajusta el paso siguiente.

### 2.5. Configura las credenciales (`.env`)
El proyecto **no** trae las contraseñas escritas en el código; las lee de un archivo `.env`.
```bash
cp .env.example .env
```
Ábrelo y revisa que coincida con lo que creaste en el paso anterior:
```ini
DB_NAME=canaveral_db
DB_USER=canaveral_user
DB_PASSWORD=canaveral2025
DB_HOST=localhost
DB_PORT=5432
```
> Si tu PostgreSQL corre en otro puerto o quieres usar tu propio usuario, cambia estos
> valores — no toques `settings.py`.

### 2.6. Crea las tablas (migraciones)
```bash
python manage.py migrate
```
Esto crea, en orden:
1. Las tablas propias de Django (usuarios del admin, sesiones).
2. Las **16 tablas de Supertiendas Cañaveral** con todas sus restricciones.
3. Los nombres de llave primaria/foránea del DDL, con sus reglas `ON DELETE`/`ON UPDATE`.
4. Las **3 vistas** y los **2 triggers de PL/pgSQL** (ver secciones 5 y 6).

Si ves `Applying supermercado.0002_ddl_vistas_triggers... OK` al final, quedó todo listo.

### 2.7. Genera los datos sintéticos
```bash
python manage.py generar_datos
```
Tarda unos segundos y va imprimiendo cuántos registros crea de cada tabla. Al final verás
algo como:
```
TOTAL: 5599 registros
Registros transaccionales: 3194 (mínimo exigido: 1.000)
```
Si quieres empezar de cero otra vez (por ejemplo, tras cambiar el generador):
```bash
python manage.py generar_datos --limpiar
```

### 2.8. Prende el servidor
```bash
python manage.py runserver
```
Abre en el navegador:
- **App web:** http://127.0.0.1:8000/
- **Panel de administración:** http://127.0.0.1:8000/admin/
  (para entrar aquí necesitas un usuario: `python manage.py createsuperuser`)

Con eso ya está corriendo todo.

---

## 3. Qué trae la carpeta (mapa del proyecto)

```
Supertiendas-Canaveral/
│
├── canaveral/                    # Configuración global de Django
│   ├── settings.py               #   Conexión a PostgreSQL, lee el .env
│   └── urls.py                   #   Conecta las rutas "/" y "/admin/"
│
├── supermercado/                 # La app: todo el negocio vive aquí
│   ├── models.py                 #   Las 16 tablas, como clases de Python
│   ├── views.py                  #   La lógica de cada página (qué hace cada botón)
│   ├── forms.py                  #   Los formularios y sus validaciones
│   ├── urls.py                   #   Las rutas de la app (/clientes/, /facturas/, etc.)
│   ├── admin.py                  #   Qué se ve en /admin/
│   ├── consultas.py              #   Las 20 consultas SQL, escritas a mano
│   ├── migrations/
│   │   ├── 0001_initial.py               # Crea las tablas
│   │   └── 0002_ddl_vistas_triggers.py   # Ajusta nombres + crea vistas y triggers
│   └── management/commands/
│       ├── generar_datos.py              # Genera los datos sintéticos
│       └── consultas_validacion.py       # Corre las 20 consultas por consola
│
├── templates/supermercado/       # Las páginas HTML (una por pantalla)
│
├── sql/                          # Los mismos scripts, en SQL puro (por si no usas Django)
│   ├── 01_ddl_supertiendas_canaveral.sql     # CREATE TABLE de las 16 tablas
│   ├── 02_datos_supertiendas_canaveral.sql   # INSERT de los ~5.600 registros
│   ├── 03_consultas_sql.sql                  # Las 20 consultas
│   └── 04_vistas_y_triggers.sql              # Las 3 vistas + los 2 triggers
│
├── docs/
│   ├── mer.png / mer.svg         # El diagrama entidad-relación
│   └── capturas/                 # Pantallazos de la app funcionando
│
├── DOC_IA.md                     # Registro de uso de IA (prompts, ajustes manuales)
├── README.md                     # Versión corta de esta guía
├── .env / .env.example           # Credenciales (el .env real nunca se sube a GitHub)
└── requirements.txt              # Las 3 librerías que se instalan con pip
```

**Regla mental simple:** si quieres cambiar *cómo se ve* algo → `templates/`. Si quieres
cambiar *qué hace* un botón → `views.py`. Si quieres cambiar *qué datos existen* →
`models.py` (y después tienes que migrar).

---

## 4. El esquema de la base de datos, tabla por tabla

Todo vive en el esquema `public` de PostgreSQL. Aquí va cada tabla con su propósito,
sus columnas más importantes y sus relaciones. Los nombres reales en PostgreSQL van en
**minúscula** (ej. `idcliente`), aunque en el DDL se escriban con mayúsculas por legibilidad.

### 4.1. Tablas de catálogo (no dependen de nadie)

| Tabla | Para qué sirve | Columnas clave |
|---|---|---|
| `empresa` | Los datos de Supertiendas Cañaveral como vendedor (para la factura) | `nit`, `razon_social`, `sitio_web` |
| `resolucion_dian` | La resolución de facturación autorizada | `prefijo`, `rango_desde/hasta`, `vigencia_desde/hasta` |
| `sede` | Las 16 tiendas | `nombre`, `ciudad`, `horario_apertura/cierre` |
| `categoria` | Categorías de producto (Frutas y Verduras, Licores, etc.) | `nombre` |
| `marca` | Marcas, incluida la propia (Doña Lupe) | `nombre`, `es_marca_propia` |
| `metodo_pago` | Efectivo, Nequi, PSE, etc. | `nombre` |

### 4.2. Entidades principales

**`cliente`** — persona natural o empresa que compra.
- Diferencia NATURAL/JURÍDICO con `tipo_cliente`; si es jurídico, el `tipo_documento`
  *tiene* que ser NIT (hay un `CHECK` que lo obliga).
- `habeas_data` (booleano): si no está marcado, la app no deja crear el cliente.
- Dos direcciones: `direccion_residencia` y `direccion_operativa` (esta última solo
  aplica a empresas).

**`proveedor`** — de quién compra la empresa.
- Trae RUT, banco + tipo de cuenta + número (certificación bancaria), `tipo_proveedor`,
  `tiempo_entrega_promedio` (días), `condiciones_pago` (días) y `calificacion` (1 a 5).
- Tres contactos separados: comercial, cartera y logístico.

**`producto`** — el catálogo.
- **Siempre** tiene un `proveedor` (llave foránea obligatoria, `ON DELETE RESTRICT`): no
  puedes crear un producto sin elegir un proveedor ya registrado.
- `categoria_iva` decide la tarifa (`GENERAL` 19%, `DIFERENCIAL` 5%, `EXENTO` 0%,
  `EXCLUIDO` no causa impuesto). Hay un `CHECK` que obliga a que el campo `iva` sea
  coherente con la categoría.
- `activo` (booleano) es la eliminación lógica: cuando "eliminas" un producto desde la
  app, en realidad esto pasa a `False`. La fila nunca se borra.

**`empleado`** — trabaja en una `sede` (FK obligatoria).

**`tarjeta_amarilla`** — el programa de fidelización, ligado a un `cliente`
(`ON DELETE CASCADE`: si se borra el cliente, se borra su tarjeta).

### 4.3. Inventario

**`inventario`** — cuánto hay de un `producto` en una `sede`.
- Columnas: `cantidad_disponible`, `demanda_diaria`, `stock_minimo`.
- **Importante:** aquí NO se guarda "días de stock". Eso se calcula al vuelo
  (`cantidad_disponible / demanda_diaria`) cada vez que se consulta — ni en el modelo de
  Django, ni en la vista SQL, ni en ningún lado se almacena ese número.
- Restricción `UNIQUE (producto, sede)`: un producto solo puede tener una fila de
  inventario por tienda.

### 4.4. Ventas

**`orden`** = la factura electrónica.
- Lleva `resolucion` (FK a `resolucion_dian`), `prefijo` + `numero_factura` (el
  consecutivo DIAN), `fecha_orden` y `fecha_expedicion`.
- `subtotal`, `iva` y `total`, con el `CHECK (total = subtotal + iva)` — si esto no
  cuadra exactamente, PostgreSQL rechaza la fila.
- `estado`: PENDIENTE / PAGADA / ANULADA. La app nunca deja editar ni borrar una factura
  ya creada: solo existe el botón "Anular", que cambia el estado.

**`detalle_orden`** = cada línea de la factura (un producto + cantidad).
- Aquí es donde se guarda el IVA **por ítem** (`iva_porcentaje`, `iva_valor`), porque la
  ley exige discriminarlo así, no solo en el total.
- `UNIQUE (orden, producto)`: no puedes repetir el mismo producto dos veces en una
  factura (si necesitas más, subes la cantidad).

### 4.5. Compras

**`compra`** = la orden de pedido a un proveedor.
- Siempre arranca en `estado = 'PENDIENTE'`.
- `lugar_entrega` es la bodega donde debe llegar.

**`detalle_compra`** = cada línea del pedido.
- `cantidad` tiene un `CHECK` entre 1 y 500 (la regla del enunciado).

### 4.6. El diagrama completo

Está en `docs/mer.png` (y `docs/mer.svg` si quieres verlo a más resolución). Muestra las
16 tablas con sus columnas, marcando cuáles son PK (llave primaria, en amarillo) y cuáles
son FK (llave foránea, en azul), y las líneas de relación con su cardinalidad 1:N.

---

## 5. Las 3 vistas (para no repetir SQL complicado)

Viven en `sql/04_vistas_y_triggers.sql` y las crea la migración `0002`. Son solo consultas
guardadas con nombre; las puedes usar como si fueran una tabla:

```sql
SELECT * FROM vw_dias_stock WHERE categoria_estado = 'AGOTADO';
SELECT * FROM vw_ventas_mensuales WHERE sede = 'Supertiendas Cañaveral Norte';
SELECT * FROM vw_desempeno_proveedores ORDER BY monto_comprado DESC;
```

| Vista | Qué calcula |
|---|---|
| `vw_dias_stock` | Días de stock, categoría de estado (AGOTADO/CRÍTICO/ALERTA/SEGURO) y acción recomendada, por producto y sede |
| `vw_ventas_mensuales` | Ingresos, IVA recaudado y ticket promedio por sede y por mes |
| `vw_desempeno_proveedores` | Cuántos pedidos le has hecho a cada proveedor, cuántos cumplió y cuánto le has comprado |

---

## 6. Los 2 triggers (la parte "automática")

Ambos están escritos en **PL/pgSQL** (el lenguaje de procedimientos de PostgreSQL) y se
disparan solos, sin que la app tenga que hacer nada extra.

### `trg_compra_recibida`
- Se dispara cuando una fila de `compra` cambia su `estado` a `RECIBIDA`.
- Recorre las líneas de esa compra (`detalle_compra`) y **suma** cada cantidad al
  `inventario` de la sede correspondiente. Si el producto no tenía fila de inventario en
  esa sede todavía, la crea.
- En la app: pasa cuando le das clic a "Marcar como recibida" en una orden de pedido.

### `trg_venta_descuenta_stock`
- Se dispara cada vez que se inserta una línea en `detalle_orden` (es decir, cada vez que
  facturas algo).
- **Descuenta** esa cantidad del `inventario` de la sede donde se hizo la venta, sin dejar
  que el número baje de cero.
- En la app: pasa automáticamente al generar una factura nueva.

Puedes verlos en acción así (ejemplo desde `psql`):
```sql
-- Antes de recibir
SELECT cantidaddisponible FROM inventario WHERE idproducto = 5 AND idsede = 1;

-- Marca la compra como recibida
UPDATE compra SET estado = 'RECIBIDA' WHERE idcompra = 3;

-- Después: debería haber subido
SELECT cantidaddisponible FROM inventario WHERE idproducto = 5 AND idsede = 1;
```

---

## 7. Las 20 consultas SQL

Viven en `supermercado/consultas.py` (para que la app web y la consola las compartan) y
también en `sql/03_consultas_sql.sql` en texto plano. Se dividen en:
- **1 a 10 — básicas:** un `JOIN` + `GROUP BY`, aspectos directos del negocio.
- **11 a 20 — complejas:** subconsultas, `RANK() OVER`, `NOT EXISTS`, comparación contra
  promedios, etc.

Formas de verlas:
```bash
# En el navegador
http://127.0.0.1:8000/consultas/

# En la consola, las 20
python manage.py consultas_validacion

# Solo las básicas, o solo una en particular
python manage.py consultas_validacion --grupo basicas
python manage.py consultas_validacion --n 13
```

---

## 8. Los datos sintéticos: qué hace `generar_datos`

El comando (`supermercado/management/commands/generar_datos.py`) llena la base en este
orden estricto (porque cada tabla depende de la anterior):

1. Empresa y resolución DIAN.
2. Sedes, categorías, marcas, métodos de pago.
3. **Proveedores** (antes que los productos, porque un producto los necesita).
4. Clientes y sus tarjetas.
5. Empleados (mínimo 4 por sede).
6. Productos (cada uno con su proveedor y su categoría de IVA correcta).
7. Inventario (con una mezcla realista de AGOTADO/CRÍTICO/ALERTA/SEGURO).
8. Facturas y sus líneas.
9. Órdenes de pedido y sus líneas.

Los datos no son parejos a propósito — tienen **sesgos** para que las consultas tengan
algo interesante que mostrar: 82% de facturas pagadas (12% pendientes, 6% anuladas), 78%
de ventas presenciales, la mayoría de clientes con cédula, la mayoría de proveedores bien
calificados pero unos pocos malos, etc. Todo detallado en el `README.md`.

Opciones útiles:
```bash
python manage.py generar_datos --limpiar              # borra todo y regenera
python manage.py generar_datos --seed 42              # otra semilla (resultados distintos)
python manage.py generar_datos --ordenes 1000          # más facturas
```

---

## 9. Recorrido rápido de la app (qué botón hace qué)

| Pantalla | Qué puedes hacer |
|---|---|
| **Inicio** (`/`) | Ver ingresos, facturas pagadas, gráfico de ventas por mes y alertas de stock |
| **Clientes** | Crear, buscar, editar, eliminar (bloqueado si tiene facturas) |
| **Proveedores** | Igual, más el NIT queda protegido al editar |
| **Productos** | Crear (pide proveedor obligatorio), editar, "Eliminar" = desactivar |
| **Inventario** | Ver días de stock calculados y su semáforo de estado; editar cantidades |
| **Facturas** | Crear una factura completa (elige cliente + productos + cantidades); ver detalle; anular |
| **Pedidos** | Elegir proveedor → ver solo sus productos → crear pedido; luego "Recibir" (dispara el trigger) |
| **Consultas SQL** | Ver las 20 consultas corriendo en vivo, con su SQL visible si haces clic en "Ver SQL" |
| **Admin** (`/admin/`) | Vista tipo Excel de todas las tablas, para revisar rápido sin pasar por los formularios |

---

## 10. Problemas comunes al levantarlo

**"connection refused" al migrar o correr el servidor**
→ PostgreSQL no está corriendo, o el `.env` tiene mal el host/puerto. Revisa con
`psql -h localhost -U canaveral_user -d canaveral_db` si puedes conectarte a mano.

**`ModuleNotFoundError` al correr cualquier comando**
→ Revisa que activaste el entorno virtual (`source venv/bin/activate`) y que corriste
`pip install -r requirements.txt`.

**Error de restricción (`CHECK` o `UNIQUE`) al generar datos**
→ No debería pasar (ya está probado), pero si cambiaste algo en `models.py` sin migrar,
corre `python manage.py makemigrations` y `python manage.py migrate` de nuevo.

**Quiero empezar 100% de cero**
```bash
# En psql:
DROP DATABASE canaveral_db;
CREATE DATABASE canaveral_db OWNER canaveral_user;
```
```bash
# En la terminal del proyecto:
python manage.py migrate
python manage.py generar_datos
```

---

## 11. Para la sustentación / entrega

- El **diagrama MER** ya está en `docs/mer.png`.
- Los **archivos `.sql`** de la carpeta `sql/` son la versión "en texto plano" de todo:
  úsalos si el profesor pide el código SQL directamente, sin pasar por Django.
- El **`DOC_IA.md`** ya tiene los prompts y los ajustes manuales documentados — es
  requisito obligatorio del enunciado, no lo olvides al entregar.
- Las **capturas** de `docs/capturas/` sirven como evidencia de que la app corre.
- Si te preguntan por el reto opcional: los índices están en el DDL, las vistas y los
  triggers en `sql/04_vistas_y_triggers.sql`, y puedes demostrarlos en vivo recibiendo un
  pedido o creando una factura y mostrando cómo cambia el inventario.

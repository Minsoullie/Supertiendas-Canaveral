# Proyecto Final: Sistema de Gestión Empresarial (SGE) - Bases de Datos

**Asignatura:** 750006C Bases de Datos

**Institución:** Universidad del Valle - Escuela de Ingeniería de Sistemas y Computación

**Docente:** Susana Medina Gordillo

**Semestre:** 2026-1

## 🏢 Información de la Empresa Seleccionada

- **Nombre de la Empresa:** Supertiendas Cañaveral S.A.
- **Sector Económico:** Comercio al detal — cadena de supermercados
- **Descripción breve:** Cadena de supermercados real, con presencia regional en el
  Valle del Cauca (16 tiendas: 9 en Cali y 7 en Palmira, Jamundí, Candelaria, Buga,
  Tuluá, Zarzal y Roldanillo). Vende productos de consumo masivo: alimentos frescos,
  abarrotes, aseo, licores y variedades al detal y al por mayor. Además maneja una
  marca propia (**Doña Lupe**). El sistema gestiona clientes, proveedores, productos e
  insumos, inventario por sede, facturación electrónica y órdenes de pedido.

## 👥 Integrantes del Grupo

1. Samuel Vargas Valderruten - 2537761

## 🛠️ Stack Tecnológico

- **Lenguaje:** Python 3.10+
- **Framework Web:** Django 5.1
- **Base de Datos:** PostgreSQL 16 (local para desarrollo)
- **ORM / Conector:** Django ORM + psycopg2-binary
- **Otros:** python-dotenv (credenciales por variables de entorno), pgAdmin 4
  (administración gráfica de la base de datos)

## 📐 Diseño de la Base de Datos (Avance #1)

Notación de clases UML, 16 entidades, 18 relaciones, todas 1:N. Cada entidad muestra
sus llaves primarias (PK) y foráneas (FK).

### Diagrama Entidad-Relación (DER)

![Diagrama Entidad-Relación](docs/mer.png)


### Diccionario de Datos Resumido

- **Terceros:** Gestión de clientes y proveedores (NIT/CC, RUT, certificación bancaria,
  Habeas Data según la Ley 1581 de 2012).
- **Productos/Insumos:** Catálogo con proveedor obligatorio, control de stock por sede
  (`INVENTARIO`), demanda diaria y tiempo de entrega promedio del proveedor.
- **Facturación:** Registro de ventas (`ORDEN` + `DETALLE_ORDEN`) con numeración DIAN
  y cálculo de IVA legal colombiano discriminado por ítem.
- **Órdenes de Pedido:** Gestión de compras y reabastecimiento (`COMPRA` +
  `DETALLE_COMPRA`), con actualización automática del inventario vía trigger.


## 🚀 Guía de Instalación y Ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/Minsoullie/Supertiendas-Canaveral
cd supertiendas-canaveral
```

### 2. Configurar entorno virtual

```bash
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar Base de Datos

1. Crear el rol y la base de datos en PostgreSQL:

   ```sql
   CREATE ROLE canaveral_user LOGIN PASSWORD 'canaveral2025';
   CREATE DATABASE canaveral_db OWNER canaveral_user;
   GRANT ALL PRIVILEGES ON DATABASE canaveral_db TO canaveral_user;
   ```

2. Copiar `.env.example` como `.env` y ajustar las credenciales si es necesario.

3. Crear las tablas y cargar los datos. Hay **dos rutas equivalentes**:

   **Ruta recomendada — con Django (crea tablas, vistas y triggers en un solo paso):**
   ```bash
   python manage.py migrate
   python manage.py generar_datos
   ```

   **Ruta alternativa — SQL puro, ejecutando los scripts de la carpeta `sql/` en orden:**
   ```bash
   psql -U canaveral_user -d canaveral_db -f sql/01_esquema_relacional.sql
   psql -U canaveral_user -d canaveral_db -f sql/04_vistas_y_triggers.sql
   psql -U canaveral_user -d canaveral_db -f sql/02_datos_supertiendas_canaveral.sql
   ```

### 4. Ejecutar Aplicación

```bash
# Django
python manage.py runserver
```

Abrir <http://127.0.0.1:8000/> (aplicación) y <http://127.0.0.1:8000/admin/> (panel de
administración; requiere `python manage.py createsuperuser`).

## 📄 Notas de Entrega y Funcionalidades

- **Gestión de Stock:** La aplicación calcula automáticamente el estado del inventario
  (**Agotado / Crítico / Alerta / Seguro**) mediante la vista `vw_dias_stock`. Los días
  de stock **no se almacenan**: se calculan como `inventario actual ÷ demanda diaria`.
- **Integridad:** Se implementaron restricciones de llave foránea (`ON DELETE RESTRICT`)
  para impedir la eliminación de proveedores o clientes con pedidos o facturas activas,
  y para impedir registrar un producto sin un proveedor previamente existente.
- **IVA:** El sistema soporta las cuatro categorías de la legislación colombiana —
  **19%, 5%, 0% (exento) y Excluidos** (estos últimos no causan el impuesto).
- **Automatización (PL/pgSQL):** Dos triggers mantienen el inventario sincronizado sin
  intervención manual: `trg_compra_recibida` (suma stock al recibir un pedido) y
  `trg_venta_descuenta_stock` (descuenta stock al facturar).
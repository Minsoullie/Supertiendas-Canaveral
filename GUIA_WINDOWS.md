# Guía de instalación en Windows — Supertiendas Cañaveral

Guía completa, de cero a la app corriendo en el navegador. Está pensada para Windows 10 u 11.

Al final tendrás:
- La base de datos PostgreSQL creada y cargada con ~5.600 registros.
- La aplicación web corriendo en `http://127.0.0.1:8000/`.
- pgAdmin conectado para revisar las tablas gráficamente.

**Tiempo estimado:** 30–40 minutos (la mayor parte son las descargas).

---

# PARTE 1 — Programas que tienes que instalar

Son **dos** obligatorios (Python y PostgreSQL) y uno opcional (Git).

## 1.1. Python

1. Ve a <https://www.python.org/downloads/windows/> y descarga el instalador
   **Windows installer (64-bit)** de la versión 3.12 (o cualquiera 3.10+).
2. Ejecuta el instalador.
3. ⚠️ **MUY IMPORTANTE:** en la primera pantalla, marca la casilla de abajo que dice
   **"Add python.exe to PATH"** antes de darle a *Install Now*.
   Si no la marcas, Windows no va a reconocer el comando `python` y te va a tocar
   reinstalar.
4. Dale a **Install Now** y espera.

**Verifica que quedó bien:** abre **PowerShell** (botón de Inicio → escribe "PowerShell"
→ Enter) y escribe:
```powershell
python --version
```
Debe responder algo como `Python 3.12.4`. Si dice *"no se reconoce como un comando"*,
reinstala marcando la casilla del PATH.

---

## 1.2. PostgreSQL (incluye pgAdmin)

1. Ve a <https://www.postgresql.org/download/windows/> y haz clic en
   **"Download the installer"** (te lleva a la página de EDB).
2. Descarga la versión **16.x** para Windows x86-64.
3. Ejecuta el instalador y ve dándole *Next*. Cuando llegues a los pasos importantes:

   - **Select Components:** deja marcado todo, sobre todo:
     - ✅ PostgreSQL Server
     - ✅ **pgAdmin 4** (la interfaz gráfica; la necesitas para el entregable)
     - ✅ **Command Line Tools** (te da el comando `psql`)
   - **Password:** te pide una contraseña para el superusuario `postgres`.
     👉 **Anótala en algún lado, la vas a necesitar.** Por ejemplo: `postgres123`.
   - **Port:** déjalo en **5432** (el que viene por defecto).
   - **Locale:** déjalo en *Default locale*.

4. Termina la instalación. Si al final te ofrece abrir *Stack Builder*, dale **Cancelar**
   (no lo necesitas).

**Verifica que quedó bien:** en el menú Inicio busca **"pgAdmin 4"** y ábrelo. Te va a
pedir una contraseña maestra (invéntate una y anótala; es solo de pgAdmin). Deberías ver
en el panel izquierdo un servidor llamado *PostgreSQL 16*.

---

## 1.3. Git (opcional, pero lo necesitas para el entregable)

El proyecto pide un repositorio público en GitHub con commits de todos los integrantes.

1. Descarga desde <https://git-scm.com/download/win>.
2. Ejecuta el instalador y dale *Next* a todo (las opciones por defecto están bien).

**Verifica:** en PowerShell, `git --version`.

---

# PARTE 2 — Preparar el proyecto

## 2.1. Descomprime el proyecto

Descomprime `Supertiendas-Canaveral.zip` en una carpeta fácil de encontrar, por ejemplo:
```
C:\Users\TuUsuario\Documentos\Supertiendas-Canaveral
```

> 💡 **Consejo:** evita rutas con espacios raros o carpetas de OneDrive sincronizadas, a
> veces dan problemas. Documentos está bien.

## 2.2. Abre PowerShell EN la carpeta del proyecto

La forma más fácil:
1. Abre la carpeta `Supertiendas-Canaveral` en el Explorador de archivos.
2. Haz clic en la barra de direcciones (donde sale la ruta), bórrala y escribe `powershell`
   + Enter.

Se abre PowerShell ya ubicado en esa carpeta. Confirma que estás en el lugar correcto:
```powershell
dir
```
Debes ver `manage.py`, `requirements.txt`, `README.md`, y las carpetas `canaveral`,
`supermercado`, `sql`, `docs`.

---

## 2.3. Crea el entorno virtual e instala las librerías

```powershell
python -m venv venv
```

Ahora hay que **activarlo**. En PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```

### ⚠️ Si te sale un error de "ejecución de scripts está deshabilitada"

Es el problema más común de Windows. PowerShell bloquea los scripts por seguridad. Tienes
dos salidas:

**Opción A (recomendada):** permite scripts solo en esta ventana:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
y vuelve a correr `.\venv\Scripts\Activate.ps1`.

**Opción B:** usa el **Símbolo del sistema (cmd)** en vez de PowerShell, donde se activa
con:
```cmd
venv\Scripts\activate.bat
```

**Sabrás que funcionó** porque al principio de la línea aparece `(venv)`:
```
(venv) PS C:\Users\TuUsuario\Documentos\Supertiendas-Canaveral>
```

Ahora instala las 3 librerías del proyecto:
```powershell
pip install -r requirements.txt
```
Esto instala **Django**, **psycopg2-binary** (el conector a PostgreSQL) y **python-dotenv**.

> ⚠️ **Importante:** cada vez que abras una terminal nueva para trabajar en el proyecto,
> tienes que volver a activar el entorno (`.\venv\Scripts\Activate.ps1`). Si ves errores
> de "No module named django", casi siempre es porque olvidaste esto.

---

# PARTE 3 — Crear la base de datos

Tienes dos caminos. Elige **uno**.

## Camino A — Con pgAdmin (más visual, recomendado)

1. Abre **pgAdmin 4**.
2. En el panel izquierdo, despliega **Servers → PostgreSQL 16**. Te pide la contraseña del
   usuario `postgres` (la que anotaste en el paso 1.2).
3. Haz clic derecho sobre **PostgreSQL 16** → **Query Tool**.
4. Pega esto y dale al botón ▶ (o F5):

```sql
CREATE ROLE canaveral_user LOGIN PASSWORD 'canaveral2025';
CREATE DATABASE canaveral_db OWNER canaveral_user;
GRANT ALL PRIVILEGES ON DATABASE canaveral_db TO canaveral_user;
```

5. Debe decir que se ejecutó correctamente. Refresca (clic derecho en *Databases* →
   *Refresh*) y verás **canaveral_db** en la lista.

## Camino B — Con la consola (SQL Shell)

1. Menú Inicio → busca **"SQL Shell (psql)"** y ábrelo.
2. Te pregunta varias cosas: dale **Enter** a todas (Server, Database, Port, Username) para
   aceptar los valores por defecto, y escribe la **contraseña de `postgres`** cuando la pida.
3. Pega los mismos tres comandos SQL de arriba (uno por uno, cada uno terminado en `;`).
4. Escribe `\q` para salir.

---

# PARTE 4 — Configurar y arrancar el proyecto

Vuelve a tu PowerShell con `(venv)` activado, en la carpeta del proyecto.

## 4.1. Crea el archivo `.env`

```powershell
copy .env.example .env
```

Ábrelo con el Bloc de notas para revisarlo:
```powershell
notepad .env
```

Debe verse así:
```ini
DJANGO_SECRET_KEY=cambia-esta-llave-en-produccion
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=canaveral_db
DB_USER=canaveral_user
DB_PASSWORD=canaveral2025
DB_HOST=localhost
DB_PORT=5432
```

Si en el Paso 3 usaste **otro nombre de usuario, otra contraseña u otro puerto**, cámbialos
aquí. Guarda y cierra.

> 🔒 Este archivo tiene las contraseñas y por eso está en el `.gitignore`: **no se sube a
> GitHub**. El que sí se sube es `.env.example`.

## 4.2. Crea las tablas

```powershell
python manage.py migrate
```

Vas a ver una lista larga de líneas terminando en `OK`. Las dos importantes son las últimas:
```
Applying supermercado.0001_initial... OK
Applying supermercado.0002_ddl_vistas_triggers... OK
```

Esto creó: las **16 tablas**, sus restricciones, las **3 vistas** y los **2 triggers de
PL/pgSQL**.

## 4.3. Carga los datos sintéticos

```powershell
python manage.py generar_datos
```

Tarda unos segundos. Al final debe decir:
```
TOTAL: 5599 registros
Registros transaccionales: 3194 (mínimo exigido: 1.000)
```

## 4.4. Crea un usuario para el panel de administración

```powershell
python manage.py createsuperuser
```
Te pide usuario, correo (puedes dejarlo vacío) y contraseña (no se ve mientras escribes,
es normal). Esto es solo para entrar a `/admin/`.

## 4.5. ¡Arranca la aplicación!

```powershell
python manage.py runserver
```

Verás:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

Abre el navegador en **<http://127.0.0.1:8000/>** 🎉

Para apagar el servidor: `Ctrl + C` en la terminal.

---

# PARTE 5 — Verifica que todo funciona

Recorre estas pantallas y confirma que cargan con datos:

| Ruta | Qué deberías ver |
|---|---|
| <http://127.0.0.1:8000/> | Panel con ingresos, gráfico de ventas por mes y alertas de stock |
| `/clientes/` | Lista de 400 clientes con su documento, ciudad y habeas data |
| `/proveedores/` | 35 proveedores con RUT, banco, calificación 1–5 |
| `/productos/` | 220 productos, cada uno con su proveedor y su categoría de IVA |
| `/inventario/` | Días de stock calculados y el semáforo AGOTADO/CRÍTICO/ALERTA/SEGURO |
| `/facturas/` | 600 facturas; entra a una para ver la Factura Electrónica de Venta completa |
| `/pedidos/` | Órdenes de pedido; las PENDIENTES tienen botón "Recibir" |
| `/consultas/` | Las 20 consultas SQL corriendo en vivo |
| `/admin/` | Panel de administración (usa el superusuario del paso 4.4) |

### Prueba el trigger de PL/pgSQL (el "reto opcional")

Vale la pena verlo funcionar, porque es lo que puedes demostrar en vivo en la sustentación:

1. Ve a `/pedidos/` y busca una orden en estado **PENDIENTE**.
2. Entra a ella y anota qué productos y cantidades tiene.
3. Dale a **"Marcar como recibida"**.
4. Ve a `/inventario/`, busca uno de esos productos en esa sede: **el stock subió solo.**
   Nadie lo actualizó desde Python — lo hizo el trigger `trg_compra_recibida` dentro de
   PostgreSQL.

Al revés también: si creas una factura nueva en `/facturas/nueva/`, el trigger
`trg_venta_descuenta_stock` **descuenta** las unidades del inventario automáticamente.

---

# PARTE 6 — Conectar pgAdmin a la base (para el entregable)

El proyecto pide una "plataforma de administración y gestión de BD". Ya la tienes instalada:

1. Abre **pgAdmin 4** → despliega **Servers → PostgreSQL 16 → Databases → canaveral_db**.
2. Despliega **Schemas → public → Tables**: ahí están las 16 tablas.
3. Clic derecho en cualquier tabla → **View/Edit Data → All Rows** para ver su contenido.
4. Despliega también **Views** (verás `vw_dias_stock`, `vw_ventas_mensuales`,
   `vw_desempeno_proveedores`) y **Functions** (verás `fn_compra_recibida` y
   `fn_venta_descuenta_stock`).

Para correr las 20 consultas desde ahí: clic derecho en `canaveral_db` → **Query Tool** →
abre el archivo `sql\03_consultas_sql.sql` y ejecuta.

📸 **Toma pantallazos de esto**: sirven como evidencia de la "plataforma de administración"
en la entrega final.

---

# PARTE 7 — Uso diario (comandos que vas a repetir)

Cada vez que vuelvas a trabajar en el proyecto:

```powershell
# 1. Entra a la carpeta y activa el entorno
cd C:\Users\TuUsuario\Documentos\Supertiendas-Canaveral
.\venv\Scripts\Activate.ps1

# 2. Arranca el servidor
python manage.py runserver
```

Otros comandos útiles:

```powershell
# Borrar todo y regenerar los datos desde cero
python manage.py generar_datos --limpiar

# Generar más facturas
python manage.py generar_datos --limpiar --ordenes 1000

# Ver las 20 consultas por consola
python manage.py consultas_validacion

# Solo las 10 básicas, o una sola
python manage.py consultas_validacion --grupo basicas
python manage.py consultas_validacion --n 13

# Regenerar el diagrama MER (necesita Graphviz instalado, es opcional)
python generar_mer.py
```

---

# PARTE 8 — Problemas típicos en Windows y cómo resolverlos

### ❌ `python : El término 'python' no se reconoce...`
No marcaste "Add python.exe to PATH" al instalar. Reinstala Python marcando esa casilla, o
usa `py` en vez de `python` (`py -m venv venv`, `py manage.py runserver`).

### ❌ `No se puede cargar el archivo Activate.ps1 porque la ejecución de scripts está deshabilitada`
Es la política de seguridad de PowerShell. Corre esto **en esa misma ventana**:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
y vuelve a activar el entorno. (Solo afecta esa ventana; no cambia nada permanente en tu PC.)

### ❌ `ModuleNotFoundError: No module named 'django'`
Se te olvidó activar el entorno virtual. Debes ver `(venv)` al inicio de la línea. Corre
`.\venv\Scripts\Activate.ps1`.

### ❌ `connection to server at "localhost" (::1), port 5432 failed: Connection refused`
PostgreSQL no está corriendo. Abre el menú Inicio → busca **"Servicios"** → busca
**postgresql-x64-16** → clic derecho → **Iniciar**.

### ❌ `password authentication failed for user "canaveral_user"`
La contraseña del `.env` no coincide con la que pusiste al crear el rol. O bien corriges el
`.env`, o cambias la contraseña en pgAdmin (Query Tool):
```sql
ALTER ROLE canaveral_user WITH PASSWORD 'canaveral2025';
```

### ❌ `database "canaveral_db" does not exist`
No se creó la base. Vuelve a la **Parte 3**.

### ❌ `permission denied for schema public`
En PostgreSQL 15+ el usuario necesita permiso explícito sobre el esquema. En pgAdmin, en el
**Query Tool conectado a `canaveral_db`** (no a `postgres`), corre:
```sql
GRANT ALL ON SCHEMA public TO canaveral_user;
ALTER DATABASE canaveral_db OWNER TO canaveral_user;
```

### ❌ Las eñes y tildes salen raras en la consola (`Ca├▒averal`)
Es solo un tema visual de la consola de Windows, **los datos están bien guardados**. Si te
molesta, antes de correr el comando escribe:
```powershell
chcp 65001
```

### ❌ `Error: That port is already in use.`
Ya tienes otro servidor corriendo. Ciérralo con `Ctrl + C`, o usa otro puerto:
```powershell
python manage.py runserver 8001
```
(y entra a `http://127.0.0.1:8001/`)

### 🔄 Quiero empezar TODO de cero
En pgAdmin (Query Tool sobre el servidor, **no** sobre `canaveral_db`):
```sql
DROP DATABASE canaveral_db;
CREATE DATABASE canaveral_db OWNER canaveral_user;
```
Y en PowerShell:
```powershell
python manage.py migrate
python manage.py generar_datos
```

---

# PARTE 9 — Resumen de la instalación (chuleta)

```powershell
# ── UNA SOLA VEZ ────────────────────────────────────────────
# 1. Instalar Python (marcando "Add to PATH") y PostgreSQL (con pgAdmin)

# 2. En pgAdmin, Query Tool:
#    CREATE ROLE canaveral_user LOGIN PASSWORD 'canaveral2025';
#    CREATE DATABASE canaveral_db OWNER canaveral_user;
#    GRANT ALL PRIVILEGES ON DATABASE canaveral_db TO canaveral_user;

# 3. En PowerShell, dentro de la carpeta del proyecto:
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py generar_datos
python manage.py createsuperuser

# ── CADA VEZ QUE TRABAJES ───────────────────────────────────
.\venv\Scripts\Activate.ps1
python manage.py runserver
# → http://127.0.0.1:8000/
```

---

# PARTE 10 — Subirlo a GitHub (requisito del entregable)

El proyecto pide un repositorio **público**, con commits de todos los integrantes.

```powershell
git init
git add .
git commit -m "Proyecto Supertiendas Cañaveral: base de datos y app web"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/supertiendas-canaveral.git
git push -u origin main
```

⚠️ Antes de subir, **confirma que el `.env` NO se va a subir** (tiene contraseñas):
```powershell
git status
```
No debe aparecer `.env` en la lista (ya está en el `.gitignore`). Sí debe aparecer
`.env.example`, que es el que sirve de plantilla para tus compañeros.

Para que haya evidencia de trabajo en equipo, que **cada integrante haga sus propios
commits** desde su computador (aunque sea de partes pequeñas), y usen ramas por
funcionalidad si pueden (`git checkout -b feature/modulo-facturacion`).

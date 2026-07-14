# 📓 Bitácora de Uso de IA - Proyecto SGE

**Grupo:** 9

**Empresa:** Supertiendas Cañaveral S.A.


## 1. Fase de Diseño: Generación de Datos Sintéticos

- **Herramienta utilizada:** Claude (Anthropic)

- **Prompt:**
  > "Este es el código DDL de la base de datos que estoy haciendo de la empresa
  > Supertiendas Cañaveral, necesito que me ayudes con la generación de datos sintéticos,
  > si necesitas información adicional coméntame." *(complementado con: formato INSERT
  > SQL directo, mínimo 1.000 registros de transacciones, prioridad en realismo de
  > nombres, cédulas y NIT colombianos)*.

- **Resultado de la IA:** Un script que genera un archivo `.sql` con sentencias `INSERT`,
  respetando el orden de las llaves foráneas y las restricciones `CHECK`/`UNIQUE`. Incluyó
  nombres y apellidos frecuentes en Colombia, y el **dígito de verificación del NIT**
  calculado con el algoritmo oficial de la DIAN (pesos por posición, módulo 11).

- **Ajuste Manual / Validación:** La IA asumió inicialmente que Supertiendas Cañaveral era
  una empresa ficticia y generó sedes en ciudades donde la cadena no opera (Cartago,
  Yumbo, Pereira) con una marca propia inventada. Se verifico la información pública real
  de la empresa y se corrigio los datos: sus 16 tiendas están en Cali (9) y en Palmira,
  Jamundí, Candelaria, Buga, Tuluá, Zarzal y Roldanillo para mayor realismo y su marca propia real es
  **Doña Lupe**. También se reemplazo manualmente todo el cálculo monetario de `float` a
  `Decimal`.

## 2. Fase de Diseño: Ampliación del Modelo (campos exigidos por el negocio)

- **Herramienta utilizada:** Claude (Anthropic)

- **Prompt:**
  > "¿Cumplí con lo que pide el proyecto?" *(seguido del PDF de la guía de la asignatura,
  > pidiendo auditar el modelo contra el enunciado completo)*.

- **Resultado de la IA:** Identificó que el modelo original no cubría varios campos
  exigidos: Habeas Data y régimen tributario en `CLIENTE`; RUT, certificación bancaria,
  calificación y tres contactos en `PROVEEDOR`; proveedor obligatorio y demanda diaria en
  `PRODUCTO`; numeración DIAN e IVA discriminado por ítem en `ORDEN`.

- **Ajuste Manual / Validación:** Se reviso cada campo sugerido contra el enunciado
  original antes de aceptarlo (no se copió la lista completa a ciegas). Se rechazó, por
  ejemplo, almacenar los "días de stock" como columna física y en su lugar se optó por calcularlo con una vista.

## 3. Fase de Desarrollo: Integración de Django con PostgreSQL

- **Herramienta utilizada:** Claude (Anthropic)

- **Prompt:**
  > "Añádele a este proyecto de Django la base de datos Postgres y toda la generación...
  > con esos datos sintéticos"

- **Resultado de la IA:** Los 16 modelos de Django mapeados 1:1 con el DDL (mismos
  nombres de tabla y columna vía `db_column`), configuración de PostgreSQL con
  credenciales en `.env`, y una migración inicial (`makemigrations`/`migrate`).

- **Ajuste Manual / Validación:** Se detecto que Django gestiona la regla `ON DELETE` en
  Python y no la escribe en la base de datos (crea las llaves foráneas sin esa cláusula).
  Como el diseño sí exige esas reglas a nivel de motor, se escribió una segunda
  migración con SQL explícito que elimina las llaves foráneas autogeneradas y las
  recrea con los nombres y las reglas `ON DELETE`/`ON UPDATE` correctas. Se verifico la
  equivalencia comparando con `diff` las restricciones de esta base contra las del DDL
  original: coincidieron exactamente (83 de 83, cero diferencias) tras corregir a mano
  el nombre de una sola llave primaria que la IA había nombrado distinto.


### 4. Prompts para solucionar problemas simples

> "Me sale el error `ModuleNotFoundError: No module named 'django'` al correr
> `python manage.py runserver` en Windows. ¿Por qué pasa y cómo lo soluciono?"

> "Al ejecutar `.\venv\Scripts\Activate.ps1` en PowerShell me sale 'la ejecución de
> scripts está deshabilitada en este sistema'. ¿Cómo lo arreglo sin desactivar la
> seguridad de todo el equipo?"

> "PostgreSQL me da el error `permission denied for schema public` al crear una tabla
> con un usuario que no es el superusuario. ¿Qué permiso me falta otorgar?"

### 5. Prompt para documentar el código

> "Revisa los archivos de codigo y agrega docstrings y comentarios breves explicando qué
> hace cada función, qué reglas de negocio aplica y qué devuelve. No cambies la lógica
> ni el comportamiento del código, solo documenta."
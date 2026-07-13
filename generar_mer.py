"""Genera el diagrama MER (notación de clases UML) a partir de los modelos reales."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "canaveral.settings")
django.setup()

from django.apps import apps  # noqa: E402

VERDE = "#14532D"
AMARILLO = "#F5B301"
FONDO = "#FFFFFF"
LINEA = "#5B6B62"

TIPOS = {
    "AutoField": "SERIAL", "IntegerField": "INTEGER", "CharField": "VARCHAR",
    "TextField": "TEXT", "BooleanField": "BOOLEAN", "DateField": "DATE",
    "DateTimeField": "TIMESTAMP", "TimeField": "TIME", "DecimalField": "NUMERIC",
    "ForeignKey": "INTEGER",
}

modelos = apps.get_app_config("supermercado").get_models()

filas = []
aristas = []

for m in modelos:
    tabla = m._meta.db_table.upper()
    atributos = []
    for f in m._meta.fields:
        tipo = TIPOS.get(f.get_internal_type(), f.get_internal_type())
        if f.get_internal_type() == "CharField":
            tipo = f"VARCHAR({f.max_length})"
        elif f.get_internal_type() == "DecimalField":
            tipo = f"NUMERIC({f.max_digits},{f.decimal_places})"

        col = f.db_column or f.attname
        if f.primary_key:
            marca, color = "PK", AMARILLO
        elif f.is_relation:
            marca, color = "FK", "#2E6B8A"
            aristas.append((tabla, f.related_model._meta.db_table.upper()))
        else:
            marca, color = "", "#12181B"
        prefijo = (f'<FONT COLOR="{color}"><B>{marca} </B></FONT>' if marca else "")
        atributos.append(
            f'<TR><TD ALIGN="LEFT">{prefijo}'
            f'<FONT COLOR="#12181B">{col}</FONT> '
            f'<FONT COLOR="#5B6B62" POINT-SIZE="9">{tipo}</FONT></TD></TR>')

    filas.append(f'''  "{tabla}" [label=<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
      <TR><TD BGCOLOR="{VERDE}"><FONT COLOR="white" POINT-SIZE="13"><B>{tabla}</B></FONT></TD></TR>
      {''.join(atributos)}
    </TABLE>>];''')

# Cardinalidades: cada FK es una relación 1:N (1 en el destino, N en el origen)
lineas_aristas = []
for origen, destino in sorted(set(aristas)):
    lineas_aristas.append(
        f'  "{destino}" -> "{origen}" [taillabel="1", headlabel="N", '
        f'color="{LINEA}", fontsize=10, fontcolor="{LINEA}", arrowhead=none];')

dot = f'''digraph MER {{
  graph [rankdir=LR, splines=ortho, nodesep=0.5, ranksep=1.5, bgcolor="{FONDO}",
         label="Supertiendas Cañaveral S.A. — Modelo Entidad-Relación (notación de clases UML)\\nPK = llave primaria · FK = llave foránea · 1:N en cada relación",
         labelloc="t", fontsize=18, fontname="Helvetica", fontcolor="{VERDE}"];
  node  [shape=plaintext, fontname="Helvetica"];
  edge  [fontname="Helvetica"];

{chr(10).join(filas)}

{chr(10).join(lineas_aristas)}
}}
'''

os.makedirs("docs", exist_ok=True)
with open("docs/mer.dot", "w", encoding="utf-8") as f:
    f.write(dot)
print(f"MER generado: {len(filas)} entidades, {len(set(aristas))} relaciones")

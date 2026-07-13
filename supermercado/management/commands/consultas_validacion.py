"""Ejecuta las 20 consultas SQL (10 básicas + 10 complejas) en consola."""
from django.core.management.base import BaseCommand
from django.db import connection

from supermercado.consultas import CONSULTAS, ejecutar


class Command(BaseCommand):
    help = "Ejecuta las consultas SQL del proyecto (JOIN, GROUP BY, subconsultas)."

    def add_arguments(self, parser):
        parser.add_argument("--n", type=int, default=None, help="Solo esa consulta.")
        parser.add_argument("--grupo", choices=["basicas", "complejas"], default=None)
        parser.add_argument("--filas", type=int, default=8)

    def _tabla(self, columnas, filas, limite):
        anchos = [len(c) for c in columnas]
        vistas = [[("" if v is None else str(v)) for v in f] for f in filas[:limite]]
        for f in vistas:
            for i, v in enumerate(f):
                anchos[i] = max(anchos[i], len(v))
        sep = "-+-".join("-" * a for a in anchos)
        out = [" | ".join(c.ljust(anchos[i]) for i, c in enumerate(columnas)), sep]
        out += [" | ".join(v.ljust(anchos[i]) for i, v in enumerate(f)) for f in vistas]
        if len(filas) > limite:
            out.append(f"... ({len(filas) - limite} filas más)")
        return "\n".join(out)

    def handle(self, *args, **o):
        sel = [c for c in CONSULTAS
               if (o["n"] is None or c["numero"] == o["n"])
               and (o["grupo"] is None or c["grupo"] == o["grupo"])]
        for c in sel:
            self.stdout.write("")
            etiqueta = "BÁSICA" if c["grupo"] == "basicas" else "COMPLEJA"
            self.stdout.write(self.style.MIGRATE_HEADING(
                f"===== Consulta {c['numero']} [{etiqueta}]: {c['titulo']} ====="))
            self.stdout.write(f"Negocio: {c['negocio']}")
            self.stdout.write(f"Técnica: {c['tecnica']}\n")
            columnas, filas = ejecutar(c, connection)
            if not filas:
                self.stdout.write(self.style.WARNING("  (sin resultados)"))
                continue
            self.stdout.write(self._tabla(columnas, filas, o["filas"]))
            self.stdout.write(self.style.SUCCESS(f"  -> {len(filas)} fila(s)"))

"""
Generador de datos sintéticos para Supertiendas Cañaveral S.A.

La empresa es REAL (Valle del Cauca). Los datos de contexto provienen de fuentes
públicas: la cadena tiene 16 tiendas (9 en Cali y 7 en otras ciudades del Valle:
Palmira, Jamundí, Candelaria, Buga, Tuluá, Zarzal y Roldanillo) y su marca propia
es Doña Lupe.

Las transacciones (clientes, ventas, empleados, proveedores) son SINTÉTICAS: esa
información no es pública. Se generan con sesgos estadísticos intencionales.

Uso:
    python manage.py generar_datos --limpiar
    python manage.py generar_datos --ordenes 800 --seed 42
"""

import random
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from supermercado.models import (
    TARIFA_POR_CATEGORIA, Categoria, Cliente, Compra, DetalleCompra, DetalleOrden,
    Empleado, Empresa, Inventario, Marca, MetodoPago, Orden, Producto, Proveedor,
    ResolucionDian, Sede, TarjetaAmarilla,
)

CENT = Decimal("0.01")


def money(x):
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)


NOMBRES_M = ["Juan", "Carlos", "Andres", "Santiago", "Sebastian", "Camilo", "David", "Felipe",
             "Daniel", "Mateo", "Alejandro", "Nicolas", "Diego", "Julian", "Oscar", "Jorge",
             "Luis", "Miguel", "Fernando", "Ricardo", "Javier", "Esteban", "Cristian", "Fabian",
             "Hernan", "Gustavo", "Alvaro", "Wilmer", "Yeison", "Brayan", "Mauricio", "Edwin"]
NOMBRES_F = ["Maria", "Luisa", "Valentina", "Daniela", "Carolina", "Andrea", "Paola", "Laura",
             "Catalina", "Natalia", "Diana", "Angela", "Sara", "Isabella", "Manuela", "Juliana",
             "Alejandra", "Tatiana", "Marcela", "Sandra", "Claudia", "Adriana", "Yuliana",
             "Leidy", "Monica", "Patricia", "Liliana", "Gloria", "Ximena", "Viviana", "Erika"]
APELLIDOS = ["Rodriguez", "Gomez", "Gonzalez", "Martinez", "Garcia", "Lopez", "Hernandez",
             "Ramirez", "Torres", "Sanchez", "Vargas", "Munoz", "Castro", "Ortiz", "Rojas",
             "Moreno", "Jimenez", "Gutierrez", "Alvarez", "Ruiz", "Diaz", "Cardenas", "Mejia",
             "Restrepo", "Quintero", "Arias", "Salazar", "Zapata", "Cortes", "Valencia",
             "Ospina", "Agudelo", "Bolanos", "Marin", "Herrera", "Guerrero", "Perez", "Ramos",
             "Cardona", "Grajales", "Cifuentes", "Trujillo", "Escobar", "Mosquera"]

# Ciudades donde la cadena tiene presencia real
CIUDADES = ["Cali", "Palmira", "Jamundi", "Candelaria", "Buga", "Tulua", "Zarzal", "Roldanillo"]

# 16 tiendas: 9 en Cali y 7 en el resto del Valle
SEDES_DEF = [
    ("Cañaveral Norte", "Cali"), ("Cañaveral Sur", "Cali"), ("Cañaveral Centro", "Cali"),
    ("Cañaveral Versalles", "Cali"), ("Cañaveral La Flora", "Cali"),
    ("Cañaveral Ciudad Jardin", "Cali"), ("Cañaveral El Ingenio", "Cali"),
    ("Cañaveral Alameda", "Cali"), ("Cañaveral Country", "Cali"),
    ("Cañaveral Palmira", "Palmira"), ("Cañaveral Jamundi", "Jamundi"),
    ("Cañaveral Candelaria", "Candelaria"), ("Cañaveral Buga", "Buga"),
    ("Cañaveral Tulua", "Tulua"), ("Cañaveral Zarzal", "Zarzal"),
    ("Cañaveral Roldanillo", "Roldanillo"),
]

# Categorías tomadas del sitio web real de la cadena
CATEGORIAS = [
    ("Frutas y Verduras", "Productos agricolas frescos"),
    ("Carnes Frescas", "Carnicos, aves y productos del mar"),
    ("Lacteos y Huevos", "Leche, quesos, yogures y huevos"),
    ("Panaderia y Pasteleria", "Pan, tortas y reposteria"),
    ("Despensa", "Granos, enlatados y abarrotes"),
    ("Bebidas", "Gaseosas, jugos y agua"),
    ("Licores", "Cervezas, vinos y destilados"),
    ("Cuidado del Hogar", "Productos de limpieza"),
    ("Cuidado Personal", "Higiene y cuidado personal"),
    ("Snacks y Dulceria", "Pasabocas, mecato y confiteria"),
    ("Productos Congelados", "Alimentos congelados"),
    ("Mundo Mascotas", "Alimento y accesorios para mascotas"),
    ("Mundo Bebe", "Panales y cuidado del bebe"),
    ("Hogar y Variedades", "Utiles, papeleria y variedades"),
]

# Doña Lupe es la marca propia REAL de Supertiendas Cañaveral
MARCAS = [
    ("Alpina", False), ("Colanta", False), ("Zenu", False), ("Bavaria", False),
    ("Postobon", False), ("Coca-Cola", False), ("Colombina", False), ("Nutresa", False),
    ("Noel", False), ("Doria", False), ("Diana", False), ("Roa", False), ("Fruco", False),
    ("Familia", False), ("Colgate", False), ("Bimbo", False), ("Ramo", False),
    ("Quaker", False), ("Nestle", False), ("Purina", False), ("Huggies", False),
    ("Winny", False), ("Levapan", False), ("San Jorge", False), ("El Rey", False),
    ("Doña Lupe", True),
    ("Doña Lupe Seleccion", True),
    ("Doña Lupe Hogar", True),
]

METODOS_PAGO = [
    ("Efectivo", "Pago en efectivo en caja"),
    ("Tarjeta Debito", "Pago con tarjeta debito"),
    ("Tarjeta Credito", "Pago con tarjeta de credito"),
    ("Transferencia PSE", "Pago electronico PSE"),
    ("Nequi", "Billetera digital Nequi"),
    ("Daviplata", "Billetera digital Daviplata"),
    ("Bono Cañaveral", "Bono regalo de la cadena"),
]

# (nombre, idx_categoria, unidad, categoria_iva, precio_min, precio_max)
# IVA según la legislación colombiana vigente:
#   EXCLUIDO    -> alimentos básicos SIN procesar (arroz, papa, banano, carne, leche)
#   EXENTO      -> tarifa 0% que sí causa impuesto
#   DIFERENCIAL -> 5%: canasta básica procesada (café, harinas, pastas, azúcar)
#   GENERAL     -> 19%: el resto
PROD_BASE = [
    ("Banano", 1, "KG", "EXCLUIDO", 2200, 3200), ("Tomate chonto", 1, "KG", "EXCLUIDO", 2800, 4200),
    ("Papa pastusa", 1, "KG", "EXCLUIDO", 1800, 2800),
    ("Cebolla cabezona", 1, "KG", "EXCLUIDO", 2500, 3800),
    ("Aguacate Hass", 1, "KG", "EXCLUIDO", 6000, 9500),
    ("Manzana roja", 1, "KG", "EXCLUIDO", 7000, 11000),
    ("Zanahoria", 1, "KG", "EXCLUIDO", 2000, 3000),
    ("Limon Tahiti", 1, "KG", "EXCLUIDO", 3500, 5500),
    ("Pechuga de pollo", 2, "KG", "EXCLUIDO", 12000, 16000),
    ("Carne de res molida", 2, "KG", "EXCLUIDO", 18000, 24000),
    ("Costilla de cerdo", 2, "KG", "EXCLUIDO", 14000, 19000),
    ("Filete de tilapia", 2, "KG", "EXCLUIDO", 20000, 27000),
    ("Muslo de pollo", 2, "KG", "EXCLUIDO", 8000, 12000),
    ("Leche entera 1L", 3, "LT", "EXCLUIDO", 3600, 4800),
    ("Queso campesino 500g", 3, "GR", "EXENTO", 9000, 13000),
    ("Yogur natural 1L", 3, "LT", "DIFERENCIAL", 6500, 9000),
    ("Huevos AA x30", 3, "UND", "EXCLUIDO", 14000, 19000),
    ("Kumis 1L", 3, "LT", "DIFERENCIAL", 5500, 7500),
    ("Pan tajado grande", 4, "UND", "DIFERENCIAL", 4500, 6500),
    ("Pan de yuca x10", 4, "UND", "DIFERENCIAL", 5000, 7000),
    ("Ponque casero", 4, "UND", "GENERAL", 8000, 12000),
    ("Croissant x6", 4, "UND", "DIFERENCIAL", 7000, 10000),
    ("Arroz blanco 500g", 5, "GR", "EXCLUIDO", 2200, 3200),
    ("Frijol cargamanto 500g", 5, "GR", "EXCLUIDO", 4500, 6500),
    ("Lenteja 500g", 5, "GR", "EXCLUIDO", 3800, 5200),
    ("Aceite girasol 1L", 5, "LT", "GENERAL", 9000, 13000),
    ("Panela cuadrada 500g", 5, "GR", "DIFERENCIAL", 3000, 4500),
    ("Sal refinada 1kg", 5, "KG", "GENERAL", 1800, 2800),
    ("Azucar blanca 1kg", 5, "KG", "DIFERENCIAL", 4200, 5800),
    ("Pasta espagueti 500g", 5, "GR", "DIFERENCIAL", 2800, 4200),
    ("Harina de maiz 1kg", 5, "KG", "DIFERENCIAL", 3500, 5000),
    ("Atun en lata 170g", 5, "GR", "GENERAL", 4500, 7000),
    ("Cafe molido 500g", 5, "GR", "DIFERENCIAL", 12000, 18000),
    ("Gaseosa 1.5L", 6, "LT", "GENERAL", 4000, 6000),
    ("Agua sin gas 600ml", 6, "ML", "GENERAL", 1800, 2800),
    ("Jugo de caja 1L", 6, "LT", "GENERAL", 3500, 5000),
    ("Gaseosa lata 330ml", 6, "ML", "GENERAL", 2500, 3800),
    ("Cerveza lata 330ml", 7, "ML", "GENERAL", 3000, 4500),
    ("Cerveza six pack", 7, "UND", "GENERAL", 15000, 22000),
    ("Vino tinto 750ml", 7, "ML", "GENERAL", 25000, 45000),
    ("Aguardiente 750ml", 7, "ML", "GENERAL", 35000, 55000),
    ("Detergente en polvo 1kg", 8, "KG", "GENERAL", 9000, 14000),
    ("Jabon loza 500g", 8, "GR", "DIFERENCIAL", 4000, 6500),
    ("Limpiador multiusos 1L", 8, "LT", "GENERAL", 5000, 8000),
    ("Papel higienico x12", 8, "UND", "GENERAL", 14000, 20000),
    ("Blanqueador 1L", 8, "LT", "GENERAL", 3500, 5500),
    ("Shampoo 400ml", 9, "ML", "GENERAL", 12000, 18000),
    ("Jabon de bano x3", 9, "UND", "DIFERENCIAL", 6000, 9500),
    ("Crema dental 100ml", 9, "ML", "GENERAL", 5000, 8000),
    ("Desodorante rollon", 9, "UND", "GENERAL", 9000, 14000),
    ("Papas fritas 150g", 10, "GR", "GENERAL", 4500, 7000),
    ("Galletas surtidas 300g", 10, "GR", "GENERAL", 5000, 8000),
    ("Chocolatina x6", 10, "UND", "GENERAL", 6000, 9000),
    ("Mani salado 200g", 10, "GR", "GENERAL", 4000, 6000),
    ("Nuggets congelados 500g", 11, "GR", "GENERAL", 12000, 17000),
    ("Papa a la francesa 1kg", 11, "KG", "GENERAL", 8000, 12000),
    ("Helado litro", 11, "LT", "GENERAL", 10000, 15000),
    ("Concentrado perro 2kg", 12, "KG", "GENERAL", 22000, 32000),
    ("Arena para gato 4kg", 12, "KG", "GENERAL", 15000, 22000),
    ("Panales etapa 3 x40", 13, "UND", "DIFERENCIAL", 32000, 42000),
    ("Panitos humedos x100", 13, "UND", "DIFERENCIAL", 8000, 12000),
    ("Cuaderno cosido 100h", 14, "UND", "GENERAL", 3500, 5500),
    ("Boligrafo negro x3", 14, "UND", "GENERAL", 3000, 5000),
    ("Resma papel carta", 14, "UND", "GENERAL", 15000, 22000),
]

PRESENTACIONES = ["", " Premium", " Familiar", " Economico", " Tradicional",
                  " Clasico", " Extra", " Seleccion", " Ahorro", " Light"]

CARGOS = [("Cajero", 1423500, 1900000), ("Auxiliar de Bodega", 1423500, 1800000),
          ("Vendedor", 1423500, 2100000), ("Surtidor", 1423500, 1700000),
          ("Domiciliario", 1423500, 1750000), ("Supervisor de Piso", 2200000, 3200000),
          ("Analista de Inventario", 2500000, 3800000), ("Jefe de Compras", 3500000, 5500000),
          ("Administrador de Sede", 4500000, 7000000)]

BANCOS = ["Bancolombia", "Davivienda", "Banco de Bogota", "BBVA Colombia",
          "Banco de Occidente", "Banco Popular", "Scotiabank Colpatria", "Banco Agrario"]

BODEGAS = ["Bodega Central - Yumbo", "Bodega Norte - Cali", "Bodega Sur - Jamundi",
           "Bodega Palmira", "Bodega Tulua", "Centro de Acopio - Buga"]

PESOS_DV = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]


def digito_verificacion(numero: str) -> int:
    """Dígito de verificación del NIT según el algoritmo oficial de la DIAN."""
    suma = sum(int(d) * PESOS_DV[i] for i, d in enumerate(reversed(numero)))
    r = suma % 11
    return r if r in (0, 1) else 11 - r


class Command(BaseCommand):
    help = "Genera datos sintéticos con sesgos estadísticos para Supertiendas Cañaveral."

    def add_arguments(self, parser):
        parser.add_argument("--limpiar", action="store_true")
        parser.add_argument("--seed", type=int, default=2025)
        parser.add_argument("--clientes", type=int, default=400)
        parser.add_argument("--proveedores", type=int, default=35)
        parser.add_argument("--empleados", type=int, default=110)
        parser.add_argument("--productos", type=int, default=220)
        parser.add_argument("--tarjetas", type=int, default=250)
        parser.add_argument("--ordenes", type=int, default=600)
        parser.add_argument("--compras", type=int, default=120)

    # -- utilidades ----------------------------------------------------------
    def _fecha(self, a, b):
        return a + timedelta(days=random.randint(0, (b - a).days))

    def _celular(self):
        return ("3" + str(random.choice([0, 1, 2, 5]))
                + str(random.choice([0, 1, 2, 4, 5, 6, 7, 8, 9]))
                + "".join(str(random.randint(0, 9)) for _ in range(7)))

    def _fijo(self):
        return "60" + str(random.choice([1, 2, 4, 5, 6, 7, 8])) + "".join(
            str(random.randint(0, 9)) for _ in range(7))

    def _nit(self, usados):
        while True:
            base = "9" + "".join(str(random.randint(0, 9)) for _ in range(8))
            nit = f"{base}-{digito_verificacion(base)}"
            if nit not in usados:
                usados.add(nit)
                return nit

    def _cedula(self, usados, tipo="CC"):
        while True:
            if tipo == "TI":
                n = "10" + "".join(str(random.randint(0, 9)) for _ in range(8))
            elif tipo in ("CE", "PP"):
                n = "".join(str(random.randint(0, 9)) for _ in range(random.choice([6, 7])))
            else:
                n = (str(random.choice([1, 6, 7, 8, 9, 10]))
                     + "".join(str(random.randint(0, 9)) for _ in range(random.choice([7, 8]))))
            if n not in usados:
                usados.add(n)
                return n

    def _email(self, a, b, usados, empresa=False):
        base = f"{a.lower()}.{b.lower()}".replace(" ", "").replace("ñ", "n")
        doms = (["empresa.com.co", "corp.co"] if empresa
                else ["gmail.com", "hotmail.com", "outlook.com", "yahoo.com"])
        while True:
            e = f"{base}{random.randint(1, 9999)}@{random.choice(doms)}"
            if e not in usados:
                usados.add(e)
                return e

    # -- comando -------------------------------------------------------------
    @transaction.atomic
    def handle(self, *args, **o):
        random.seed(o["seed"])

        if o["limpiar"]:
            self.stdout.write("Limpiando datos existentes...")
            with connection.cursor() as cur:
                cur.execute("ALTER TABLE detalle_orden DISABLE TRIGGER trg_venta_descuenta_stock;")
            for modelo in (DetalleOrden, DetalleCompra, Orden, Compra, Inventario,
                           TarjetaAmarilla, Producto, Empleado, Cliente, Proveedor,
                           MetodoPago, Marca, Categoria, Sede, ResolucionDian, Empresa):
                modelo.objects.all().delete()
            with connection.cursor() as cur:
                cur.execute("ALTER TABLE detalle_orden ENABLE TRIGGER trg_venta_descuenta_stock;")

        docs, emails = set(), set()

        # ---------------- Empresa y resolución DIAN ------------------------
        empresa = Empresa.objects.create(
            nit="890303025-1", razon_social="SUPERTIENDAS CAÑAVERAL S.A.",
            direccion="Calle 9 # 50-25", ciudad="Cali", telefono="6023320000",
            email="mercadeo.digital@stcanaveral.com",
            sitio_web="www.supertiendascanaveral.com.co")
        resolucion = ResolucionDian.objects.create(
            numero_resolucion="18764092837465", prefijo="SC",
            rango_desde=1000, rango_hasta=99999,
            vigencia_desde=date(2025, 1, 1), vigencia_hasta=date(2026, 12, 31))
        self.stdout.write(self.style.SUCCESS(
            f"  Empresa: {empresa.razon_social} · Resolución DIAN prefijo {resolucion.prefijo}"))

        # ---------------- Catálogos ----------------------------------------
        sedes = Sede.objects.bulk_create([
            Sede(nombre=f"Supertiendas {n}",
                 direccion=f"Cra {random.randint(1, 80)} # {random.randint(1, 60)}-{random.randint(1, 99)}",
                 ciudad=ciu, departamento="Valle del Cauca", telefono=self._fijo(),
                 horario_apertura=time(random.choice([7, 8]), 0),
                 horario_cierre=time(random.choice([20, 21, 22]), 0))
            for n, ciu in SEDES_DEF])
        categorias = Categoria.objects.bulk_create(
            [Categoria(nombre=n, descripcion=d) for n, d in CATEGORIAS])
        marcas = Marca.objects.bulk_create(
            [Marca(nombre=n, es_marca_propia=p) for n, p in MARCAS])
        metodos = MetodoPago.objects.bulk_create(
            [MetodoPago(nombre=n, descripcion=d) for n, d in METODOS_PAGO])
        self.stdout.write(self.style.SUCCESS(
            f"  Catálogos: {len(sedes)} sedes · {len(categorias)} categorías · "
            f"{len(marcas)} marcas · {len(metodos)} métodos de pago"))

        # ---------------- Proveedores (ANTES que los productos) ------------
        nits = set()
        proveedores_obj = []
        for _ in range(o["proveedores"]):
            tipo_emp = random.choice(["Distribuidora", "Comercializadora", "Alimentos",
                                      "Productos", "Industrias", "Suministros", "Importadora"])
            ape = random.choice(APELLIDOS)
            nit = self._nit(nits)
            proveedores_obj.append(Proveedor(
                tipo_documento="NIT", nit=nit,
                razon_social=f"{tipo_emp} {ape} {random.choice(['S.A.S', 'S.A.', 'LTDA'])}",
                rut=nit.split("-")[0],
                regimen_tributario="RESPONSABLE",
                representante_legal=f"{random.choice(NOMBRES_M + NOMBRES_F)} {random.choice(APELLIDOS)}",
                habeas_data=True,
                ciudad=random.choice(CIUDADES),
                direccion=f"Cll {random.randint(1, 90)} # {random.randint(1, 50)}-{random.randint(1, 99)}",
                telefono=self._fijo(), email=self._email(tipo_emp, ape, emails, True),
                banco=random.choice(BANCOS),
                tipo_cuenta=random.choice(["AHORROS", "CORRIENTE"]),
                numero_cuenta="".join(str(random.randint(0, 9)) for _ in range(11)),
                tipo_proveedor=random.choices(
                    ["PRODUCTO_TERMINADO", "MATERIA_PRIMA", "EMPAQUES", "ASEO", "SERVICIOS"],
                    weights=[55, 20, 10, 10, 5])[0],
                tiempo_entrega_promedio=random.choices([2, 3, 5, 7, 10, 15, 20],
                                                       weights=[10, 15, 25, 25, 15, 7, 3])[0],
                condiciones_pago=random.choice([15, 30, 30, 45, 60, 90]),
                # SESGO: la mayoría cumple; unos pocos son proveedores flojos
                calificacion=random.choices([1, 2, 3, 4, 5], weights=[3, 7, 20, 40, 30])[0],
                contacto_comercial=f"{random.choice(NOMBRES_M + NOMBRES_F)} {random.choice(APELLIDOS)}",
                contacto_cartera=f"{random.choice(NOMBRES_M + NOMBRES_F)} {random.choice(APELLIDOS)}",
                contacto_logistico=f"{random.choice(NOMBRES_M + NOMBRES_F)} {random.choice(APELLIDOS)}"))
        proveedores = Proveedor.objects.bulk_create(proveedores_obj)
        self.stdout.write(self.style.SUCCESS(f"  Proveedores: {len(proveedores)}"))

        # ---------------- Clientes -----------------------------------------
        clientes_obj = []
        for _ in range(o["clientes"]):
            juridico = random.random() < 0.18           # SESGO: 18% empresas
            if juridico:
                tipo_doc, tipo_cli = "NIT", "JURIDICO"
                doc = self._nit(docs)
                razon = random.choice(["Distribuidora", "Restaurante", "Panaderia", "Cafeteria",
                                       "Tienda", "Almacen", "Comercializadora", "Inversiones"])
                nombres = f"{razon} {random.choice(APELLIDOS)}"
                apellidos = random.choice(["S.A.S", "LTDA", "& CIA"])
                rep = f"{random.choice(NOMBRES_M + NOMBRES_F)} {random.choice(APELLIDOS)}"
                email = self._email(razon, random.choice(APELLIDOS), emails, True)
                regimen = "RESPONSABLE"
                dir_op = f"Cra {random.randint(1, 90)} # {random.randint(1, 60)}-{random.randint(1, 99)}"
            else:
                tipo_cli = "NATURAL"
                tipo_doc = random.choices(["CC", "CE", "TI", "PP"], weights=[80, 8, 7, 5])[0]
                doc = self._cedula(docs, tipo_doc)
                fem = random.random() < 0.52
                nombres = random.choice(NOMBRES_F if fem else NOMBRES_M)
                if random.random() < 0.35:
                    nombres += " " + random.choice(NOMBRES_F if fem else NOMBRES_M)
                apellidos = f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
                rep = f"{nombres} {apellidos}"     # la persona se representa a sí misma
                email = self._email(nombres.split()[0], apellidos.split()[0], emails)
                regimen = "NO_RESPONSABLE"
                dir_op = None
            clientes_obj.append(Cliente(
                tipo_documento=tipo_doc, numero_documento=doc, nombres=nombres,
                apellidos=apellidos, tipo_cliente=tipo_cli, regimen_tributario=regimen,
                representante_legal=rep,
                habeas_data=random.random() < 0.93,   # SESGO: ~93% autoriza
                email=email, telefono=self._celular(), ciudad=random.choice(CIUDADES),
                direccion_residencia=f"{random.choice(['Calle', 'Carrera', 'Avenida'])} "
                                     f"{random.randint(1, 120)} # {random.randint(1, 90)}-{random.randint(1, 99)}",
                direccion_operativa=dir_op,
                fecha_registro=self._fecha(date(2021, 1, 1), date(2024, 12, 31))))
        clientes = Cliente.objects.bulk_create(clientes_obj)
        self.stdout.write(self.style.SUCCESS(f"  Clientes: {len(clientes)}"))

        # ---------------- Tarjeta Amarilla ---------------------------------
        nums, tarjetas_obj = set(), []
        for cli in random.sample(clientes, min(o["tarjetas"], len(clientes))):
            while True:
                num = "77" + "".join(str(random.randint(0, 9)) for _ in range(14))
                if num not in nums:
                    nums.add(num)
                    break
            tarjetas_obj.append(TarjetaAmarilla(
                cliente=cli, numero_tarjeta=num,
                fecha_emision=self._fecha(date(2022, 1, 1), date(2025, 6, 30)),
                puntos_acumulados=random.choices(
                    [0, random.randint(1, 500), random.randint(500, 5000)],
                    weights=[30, 45, 25])[0],
                estado=random.choices(["ACTIVA", "INACTIVA", "BLOQUEADA"],
                                      weights=[80, 15, 5])[0]))
        TarjetaAmarilla.objects.bulk_create(tarjetas_obj)
        self.stdout.write(self.style.SUCCESS(f"  Tarjetas Amarillas: {len(tarjetas_obj)}"))

        # ---------------- Empleados ----------------------------------------
        docs_emp, empleados_obj = set(), []
        for sede in sedes:                       # mínimo 4 operativos por tienda
            for _ in range(4):
                cargo, smin, smax = random.choice(CARGOS[:5])
                empleados_obj.append(Empleado(
                    sede=sede, numero_documento=self._cedula(docs_emp),
                    nombres=random.choice(NOMBRES_M + NOMBRES_F),
                    apellidos=f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}",
                    cargo=cargo, salario=money(random.randint(smin, smax)),
                    fecha_ingreso=self._fecha(date(2019, 1, 1), date(2025, 6, 30))))
        while len(empleados_obj) < o["empleados"]:
            cargo, smin, smax = random.choice(CARGOS)
            empleados_obj.append(Empleado(
                sede=random.choice(sedes), numero_documento=self._cedula(docs_emp),
                nombres=random.choice(NOMBRES_M + NOMBRES_F),
                apellidos=f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}",
                cargo=cargo, salario=money(random.randint(smin, smax)),
                fecha_ingreso=self._fecha(date(2019, 1, 1), date(2025, 6, 30))))
        empleados = Empleado.objects.bulk_create(empleados_obj)
        emp_por_sede = {s.pk: [e for e in empleados if e.sede_id == s.pk] for s in sedes}
        self.stdout.write(self.style.SUCCESS(f"  Empleados: {len(empleados)}"))

        # ---------------- Productos (cada uno con su proveedor) ------------
        barras, vistos, productos_obj = set(), set(), []
        while len(productos_obj) < o["productos"]:
            nom, cat_idx, unidad, cat_iva, pmin, pmax = random.choice(PROD_BASE)
            marca = random.choice(marcas)
            nombre = nom + random.choice(PRESENTACIONES)
            if (nombre, marca.pk) in vistos:
                continue
            vistos.add((nombre, marca.pk))
            while True:
                cb = "770" + "".join(str(random.randint(0, 9)) for _ in range(10))
                if cb not in barras:
                    barras.add(cb)
                    break
            productos_obj.append(Producto(
                categoria=categorias[cat_idx - 1], marca=marca,
                proveedor=random.choice(proveedores),      # FK obligatoria
                codigo_barras=cb, nombre=nombre,
                descripcion=f"Producto de {CATEGORIAS[cat_idx - 1][0].lower()}",
                precio_venta=money(random.randint(pmin, pmax)),
                unidad_medida=unidad, categoria_iva=cat_iva,
                iva=TARIFA_POR_CATEGORIA[cat_iva],
                # SESGO: ~4% descontinuado (demuestra la eliminación lógica)
                activo=random.random() > 0.04))
        productos = Producto.objects.bulk_create(productos_obj)
        activos = [p for p in productos if p.activo]
        self.stdout.write(self.style.SUCCESS(
            f"  Productos: {len(productos)} ({len(activos)} activos)"))

        # ---------------- Inventario (con demanda diaria) ------------------
        inventario_obj = []
        for prod in productos:
            for sede in random.sample(sedes, random.randint(3, 9)):
                demanda = Decimal(str(round(random.uniform(0.5, 25.0), 2)))
                # Mezcla realista de estados de stock (AGOTADO / CRITICO / ALERTA / SEGURO)
                perfil = random.choices(["agotado", "critico", "alerta", "seguro"],
                                        weights=[4, 12, 26, 58])[0]
                if perfil == "agotado":
                    cant = 0
                elif perfil == "critico":
                    cant = int(demanda * Decimal(str(random.uniform(0.5, 4.5))))
                elif perfil == "alerta":
                    cant = int(demanda * Decimal(str(random.uniform(5.5, 14.5))))
                else:
                    cant = int(demanda * Decimal(str(random.uniform(16, 60))))
                inventario_obj.append(Inventario(
                    producto=prod, sede=sede, cantidad_disponible=max(0, cant),
                    demanda_diaria=demanda, stock_minimo=random.choice([5, 10, 15, 20])))
        Inventario.objects.bulk_create(inventario_obj)
        self.stdout.write(self.style.SUCCESS(f"  Inventario: {len(inventario_obj)}"))

        # ---------------- Facturas de venta --------------------------------
        tz = timezone.get_current_timezone()
        consecutivo = resolucion.rango_desde
        ordenes_obj, lineas_pend = [], []
        for _ in range(o["ordenes"]):
            sede = random.choice(sedes)
            f = self._fecha(date(2024, 1, 1), date(2025, 12, 28))
            fecha = datetime(f.year, f.month, f.day, random.randint(7, 21),
                             random.randint(0, 59), random.randint(0, 59))
            if timezone.is_naive(fecha):
                fecha = timezone.make_aware(fecha, tz)

            n = random.choices([1, 2, 3, 4, 5, 6, 7], weights=[15, 24, 23, 17, 11, 6, 4])[0]
            elegidos = random.sample(activos, min(n, len(activos)))
            subtotal, iva_total, lineas = Decimal("0.00"), Decimal("0.00"), []
            for prod in elegidos:
                cant = random.choices([1, 2, 3, 4, 5, 6, 8, 10, 12],
                                      weights=[33, 24, 15, 8, 6, 5, 4, 3, 2])[0]
                sub = money(prod.precio_venta * cant)
                tarifa = prod.iva if prod.causa_iva else Decimal("0")   # EXCLUIDO: no causa IVA
                iva_linea = money(sub * tarifa / Decimal(100))
                subtotal += sub
                iva_total += iva_linea
                lineas.append((prod, cant, prod.precio_venta, sub, tarifa, iva_linea))

            ordenes_obj.append(Orden(
                resolucion=resolucion, prefijo=resolucion.prefijo, numero_factura=consecutivo,
                cliente=random.choice(clientes),
                empleado=random.choice(emp_por_sede[sede.pk]),   # empleado de esa sede
                sede=sede, metodo_pago=random.choice(metodos),
                fecha_orden=fecha, fecha_expedicion=fecha,
                subtotal=subtotal, iva=iva_total, total=subtotal + iva_total,
                tipo_venta=random.choices(["PRESENCIAL", "ONLINE"], weights=[78, 22])[0],
                estado=random.choices(["PAGADA", "PENDIENTE", "ANULADA"],
                                      weights=[82, 12, 6])[0],
                cufe=f"CUFE-{resolucion.prefijo}{consecutivo:08d}"))
            lineas_pend.append(lineas)
            consecutivo += 1

        ordenes = Orden.objects.bulk_create(ordenes_obj)
        detalles = [
            DetalleOrden(orden=orden, producto=p, cantidad=c, precio_unitario=pu,
                         subtotal=sub, iva_porcentaje=tar, iva_valor=ivl)
            for orden, lineas in zip(ordenes, lineas_pend)
            for p, c, pu, sub, tar, ivl in lineas]
        # El inventario ya se generó con un perfil realista: no se descuenta el
        # histórico dos veces, así que el trigger se desactiva solo para esta carga.
        with connection.cursor() as cur:
            cur.execute("ALTER TABLE detalle_orden DISABLE TRIGGER trg_venta_descuenta_stock;")
        DetalleOrden.objects.bulk_create(detalles)
        with connection.cursor() as cur:
            cur.execute("ALTER TABLE detalle_orden ENABLE TRIGGER trg_venta_descuenta_stock;")
        self.stdout.write(self.style.SUCCESS(
            f"  Facturas: {len(ordenes)} · Ítems facturados: {len(detalles)}"))

        # ---------------- Órdenes de pedido --------------------------------
        compras_obj, dc_pend = [], []
        for _ in range(o["compras"]):
            prov = random.choice(proveedores)
            catalogo = [p for p in productos if p.proveedor_id == prov.pk]
            if not catalogo:
                continue
            elegidos = random.sample(catalogo, min(random.randint(2, 6), len(catalogo)))
            total, lineas = Decimal("0.00"), []
            for prod in elegidos:
                costo = money(prod.precio_venta
                              * Decimal(str(round(random.uniform(0.55, 0.80), 4))))
                if costo <= 0:
                    costo = money(1)
                cant = random.randint(10, 400)          # regla del negocio: 1 a 500
                total += money(costo * cant)
                lineas.append((prod, cant, costo))
            compras_obj.append(Compra(
                proveedor=prov, sede=random.choice(sedes),
                fecha_compra=self._fecha(date(2024, 1, 1), date(2025, 12, 20)),
                lugar_entrega=random.choice(BODEGAS), total=total,
                estado=random.choices(["RECIBIDA", "PENDIENTE", "CANCELADA"],
                                      weights=[70, 22, 8])[0]))
            dc_pend.append(lineas)

        compras = Compra.objects.bulk_create(compras_obj)
        dc = [DetalleCompra(compra=c, producto=p, cantidad=cant, precio_unitario=costo)
              for c, lineas in zip(compras, dc_pend) for p, cant, costo in lineas]
        DetalleCompra.objects.bulk_create(dc)
        self.stdout.write(self.style.SUCCESS(
            f"  Órdenes de pedido: {len(compras)} · Ítems pedidos: {len(dc)}"))

        total_reg = (2 + len(sedes) + len(categorias) + len(marcas) + len(metodos)
                     + len(proveedores) + len(clientes) + len(tarjetas_obj) + len(empleados)
                     + len(productos) + len(inventario_obj) + len(ordenes) + len(detalles)
                     + len(compras) + len(dc))
        transaccionales = len(ordenes) + len(detalles) + len(compras) + len(dc)
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"TOTAL: {total_reg} registros"))
        self.stdout.write(self.style.SUCCESS(
            f"Registros transaccionales: {transaccionales} (mínimo exigido: 1.000)"))

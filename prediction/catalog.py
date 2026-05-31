PRODUCTOS = [
    "Arroz",
    "Azúcar",
    "Fideos",
    "Aceite",
    "Harina",
    "Sal",
    "Atún",
    "Durazno",
    "Leche",
    "Galletas",
    "Mermelada",
    "Mantequilla",
    "Margarina",
    "Café",
    "Cacao",
    "Chocolate",
    "Agua",
    "Gaseosa",
    "Jugo",
    "Cerveza",
    "Vino",
    "Ron",
    "Sopa",
    "Puré",
    "Mayonesa",
    "Ketchup",
    "Mostaza",
    "Frijoles",
    "Lentejas",
    "Garbanzo",
]

PROVEEDORES = [
    "GrupoIntradevco",
    "DistribuidoraSantaElena",
    "ImportadoraDelPacifico",
    "AlimentosAndinos",
    "ConsorcioAlimex",
    "ComercializadoraGlobalFoods",
    "DistribuidoraElPlacer",
    "ExportadoraSolAndino",
    "LogisticaIntegralPeru",
    "ImportadoraValleSur",
]

ALMACENES = ["Almacén Central", "Almacén Norte", "Almacén Sur"]
TURNOS = ["Mañana", "Tarde", "Noche"]

# Stock base por almacén (se suma variación por producto al inicializar).
STOCK_BASE_POR_ALMACEN = {
    "Almacén Central": 120,
    "Almacén Norte": 80,
    "Almacén Sur": 60,
}

DEFAULT_CUSTOMERS = [
    {
        "name": "Comercial Los Andes",
        "email": "contacto@losandes.example",
        "phone": "+51 987 654 321",
    },
    {
        "name": "Distribuidora Lima Norte",
        "email": "ventas@limanorte.example",
        "phone": "+51 912 345 678",
    },
    {
        "name": "Minimarket El Sol",
        "email": "pedidos@elsol.example",
        "phone": "+51 999 111 222",
    },
    {
        "name": "Bodega San Martín",
        "email": None,
        "phone": "+51 934 567 890",
    },
]


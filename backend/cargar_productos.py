from database import productos

CATALOGO = [
    # Laptops
    {"nombre": "Laptop Lenovo IdeaPad 3 15\"", "descripcion": "Ryzen 5, 16 GB RAM, SSD de 512 GB y pantalla Full HD. Ideal para estudiar y trabajar.", "precio": 2299000, "stock": 8, "categoria": "Laptops"},
    {"nombre": "Laptop ASUS TUF Gaming F15", "descripcion": "Intel Core i5, 16 GB RAM, SSD de 512 GB y gráficos RTX. Pantalla de 144 Hz.", "precio": 4499000, "stock": 5, "categoria": "Laptops"},
    # Celulares
    {"nombre": "Samsung Galaxy A55 5G", "descripcion": "256 GB de almacenamiento, pantalla AMOLED de 6.6\" y cámara de 50 MP.", "precio": 1699000, "stock": 15, "categoria": "Celulares"},
    {"nombre": "Xiaomi Redmi Note 13", "descripcion": "128 GB, pantalla AMOLED de 120 Hz y carga rápida de 33 W.", "precio": 899000, "stock": 20, "categoria": "Celulares"},
    # Audio
    {"nombre": "Audífonos Sony WH-CH520", "descripcion": "Bluetooth inalámbricos con hasta 50 horas de batería y micrófono integrado.", "precio": 189000, "stock": 25, "categoria": "Audio"},
    {"nombre": "Parlante JBL Flip 6", "descripcion": "Parlante Bluetooth portátil, resistente al agua y al polvo (IP67).", "precio": 489000, "stock": 12, "categoria": "Audio"},
    # Periféricos
    {"nombre": "Teclado Mecánico Redragon Kumara", "descripcion": "Teclado mecánico compacto con switches rojos e iluminación LED.", "precio": 169000, "stock": 30, "categoria": "Periféricos"},
    {"nombre": "Mouse Logitech G203", "descripcion": "Mouse gamer con sensor de 8.000 DPI e iluminación RGB personalizable.", "precio": 99000, "stock": 40, "categoria": "Periféricos"},
    {"nombre": "Webcam Logitech C920 HD Pro", "descripcion": "Cámara web Full HD 1080p con micrófono estéreo para videollamadas.", "precio": 329000, "stock": 10, "categoria": "Periféricos"},
    # Monitores
    {"nombre": "Monitor LG 24\" Full HD IPS", "descripcion": "Panel IPS de 75 Hz con bordes delgados y tecnología AMD FreeSync.", "precio": 579000, "stock": 14, "categoria": "Monitores"},
    {"nombre": "Monitor Samsung Odyssey 27\" 165Hz", "descripcion": "Monitor gamer curvo QHD con 165 Hz y 1 ms de respuesta.", "precio": 1199000, "stock": 6, "categoria": "Monitores"},
    # Gaming
    {"nombre": "Control Inalámbrico Xbox Series", "descripcion": "Compatible con Xbox, PC y celular. Conexión Bluetooth y agarre texturizado.", "precio": 289000, "stock": 18, "categoria": "Gaming"},
    {"nombre": "Silla Gamer Ergonómica", "descripcion": "Silla reclinable con soporte lumbar, cojín de cuello y apoyabrazos ajustables.", "precio": 799000, "stock": 4, "categoria": "Gaming"},
    # Almacenamiento
    {"nombre": "SSD Kingston NV2 1 TB NVMe", "descripcion": "Unidad de estado sólido M.2 con lecturas de hasta 3.500 MB/s.", "precio": 259000, "stock": 22, "categoria": "Almacenamiento"},
    {"nombre": "Memoria USB SanDisk 128 GB", "descripcion": "Memoria USB 3.0 de alta velocidad con diseño compacto.", "precio": 39000, "stock": 50, "categoria": "Almacenamiento"},
    # Accesorios
    {"nombre": "Hub USB-C 7 en 1", "descripcion": "HDMI 4K, 3 puertos USB 3.0, lector SD/microSD y carga Power Delivery.", "precio": 119000, "stock": 28, "categoria": "Accesorios"},
    {"nombre": "Power Bank Anker 20.000 mAh", "descripcion": "Batería externa de carga rápida con dos puertos USB y uno USB-C.", "precio": 199000, "stock": 16, "categoria": "Accesorios"},
]

nuevos = 0

for producto in CATALOGO:
    resultado = productos.update_one(
        {"nombre": producto["nombre"]},
        {"$setOnInsert": {k: v for k, v in producto.items() if k != "nombre"}},
        upsert=True,
    )
    if resultado.upserted_id:
        nuevos += 1

print(f"Productos nuevos insertados: {nuevos}")
print(f"Ya existían: {len(CATALOGO) - nuevos}")
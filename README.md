# ⚡ TechGear - Tienda tecnológica

## Descripción

TechGear es una tienda en línea de productos tecnológicos con arquitectura cliente-servidor desacoplada:

- **Backend (FastAPI):** API REST que gestiona productos, usuarios, carrito y pedidos, con autenticación JWT y persistencia en MongoDB Atlas.
- **Frontend (Django):** interfaz web con plantillas HTML (Bootstrap) que consume la API y guarda el JWT en la sesión del usuario.

### Funcionalidades

- Catálogo con búsqueda y filtro por categoría.
- Registro e inicio de sesión con JWT (contraseñas encriptadas con bcrypt).
- **Cliente:** añadir productos al carrito, cambiar cantidades, eliminarlos, vaciar el carrito, confirmar el pedido y consultar "Mis pedidos".
- **Administrador:** panel con CRUD de productos, pedidos (cambio de estado) y usuarios (cambio de rol).
- Control de stock: no se pueden añadir más unidades de las disponibles y el descuento al confirmar es atómico.
- Manejo de excepciones: API caída, timeout, producto sin stock, token vencido, base de datos no disponible.

### Flujo de la aplicación

```
Navegador → Django (plantillas + sesión con JWT)
                 │  HTTP (requests)
                 ▼
            FastAPI (API REST) → MongoDB Atlas
```

## Tecnologías y librerías

| Tecnología | Uso |
|---|---|
| Python 3.12 | Lenguaje principal |
| FastAPI 0.161 | API REST del backend |
| Uvicorn | Servidor ASGI |
| Pydantic 2 / email-validator | Validación de datos |
| PyMongo 4.19 | Conexión con MongoDB Atlas |
| PyJWT | Generación y validación de tokens JWT |
| bcrypt | Encriptación de contraseñas |
| python-dotenv | Variables de entorno |
| Django 6.1 | Frontend, plantillas y sesiones |
| Requests | Comunicación Django → FastAPI |
| Bootstrap 5.3 | Estilos (por CDN) |
| MongoDB Atlas | Base de datos en la nube |
| Render / Vercel | Despliegue de la API / del frontend |

## Estructura del proyecto

```
proyectoo/
├── .env                      # Variables de entorno (NO se sube a Git)
├── .gitignore
├── README.md
├── backend/                  # API FastAPI
│   ├── main.py               # Punto de entrada y manejo global de errores
│   ├── database.py           # Conexión a MongoDB y colecciones
│   ├── seguridad.py          # Hash de contraseñas y JWT
│   ├── requirements.txt
│   ├── cargar_productos.py   # Carga el catálogo inicial
│   ├── hacer_admin.py        # Promueve un usuario a administrador
│   ├── probar_conexion.py    # Prueba la conexión a Mongo
│   ├── routes/
│   │   ├── productos.py
│   │   ├── pedidos.py
│   │   ├── usuarios.py
│   │   └── carrito.py
│   └── schemas/
│       ├── producto.py
│       ├── pedido.py
│       ├── usuario.py
│       └── carrito.py
└── techgear_web/             # Frontend Django
    ├── manage.py
    ├── config/               # settings, urls, wsgi, asgi
    └── tienda/
        ├── views.py          # Catálogo, login, registro, logout
        ├── views_cliente.py  # Carrito y mis pedidos
        ├── views_admin.py    # Panel de administración
        ├── urls.py
        ├── templatetags/
        │   └── tienda_extras.py
        └── templates/
            ├── 404.html
            ├── 500.html
            └── tienda/
                ├── base.html
                ├── productos.html
                ├── login.html
                ├── registro.html
                ├── carrito.html
                ├── mis_pedidos.html
                └── admin_*.html
```

## Instalación y ejecución (local)

### 1. Requisitos

- Python 3.12 o superior
- Git
- Una cuenta en MongoDB Atlas (cluster gratuito) con tu IP permitida en *Network Access*

### 2. Clonar e instalar

```bash
git clone [URL_DEL_REPOSITORIO]
cd proyectoo
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r backend/requirements.txt
```

### 3. Variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```
MONGO_URI=mongodb+srv://USUARIO:CONTRASEÑA@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=tienda
JWT_SECRET=una_clave_larga_y_aleatoria
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

Para generar la clave: `python -c "import secrets; print(secrets.token_hex(32))"`

### 4. Ejecutar el backend (puerto 8000)

```bash
cd backend
python cargar_productos.py                 # solo la primera vez
python -m uvicorn main:app --reload
```

### 5. Ejecutar el frontend (puerto 8001)

En otra terminal, con el entorno virtual activado:

```bash
cd techgear_web
python manage.py migrate
python manage.py runserver 8001
```

Abre `http://127.0.0.1:8001/`.

### 6. Crear un administrador

Regístrate desde `/registro/` y luego, desde `backend/`:

```bash
python hacer_admin.py tu_correo@ejemplo.com
```

Cierra sesión y vuelve a entrar para ver el **Panel Admin**.

## Endpoints principales de la API

| Método | Ruta | Acceso |
|---|---|---|
| POST | `/usuarios/registro` | Público |
| POST | `/usuarios/login` | Público (devuelve el JWT) |
| GET | `/usuarios/me` | Usuario autenticado |
| GET | `/productos/` | Público |
| POST / PUT / DELETE | `/productos/...` | Administrador |
| GET | `/carrito/` | Cliente |
| POST | `/carrito/items` | Cliente |
| PUT / DELETE | `/carrito/items/{producto_id}` | Cliente |
| DELETE | `/carrito/` | Cliente |
| POST | `/carrito/confirmar` | Cliente |
| GET | `/pedidos/mis-pedidos` | Cliente |
| GET / PUT / DELETE | `/pedidos/...`, `/usuarios/...` | Administrador |

## Manejo de excepciones

- **API caída o lenta:** Django muestra un mensaje claro en lugar de fallar (timeout de 30 s).
- **Sin stock:** la API rechaza añadir o confirmar más unidades de las disponibles; si falla un producto al confirmar, se revierte el stock ya descontado.
- **Base de datos no disponible:** FastAPI responde 503 con un mensaje legible.
- **Sesión vencida o sin permisos:** redirección al login o al catálogo con aviso.
- **Páginas 404 y 500** personalizadas.

## App desplegada

| Servicio | Plataforma | Enlace |
|---|---|---|
| Frontend (Django) | Vercel | https://taller2-pydeploy.vercel.app |
| API (FastAPI) | Render | [https://TU-API.onrender.com] |
| Documentación de la API | Render | [https://TU-API.onrender.com/docs] |

> La API usa el plan gratuito de Render: si estuvo inactiva, la primera petición puede tardar hasta un minuto.

## Autor

Alejandra londoño cantero


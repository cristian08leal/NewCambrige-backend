# WebColegios Bot

## Descripción

WebColegios Bot es una solución automatizada de extracción (scraping) e importación masiva diseñada para sincronizar datos de estudiantes y docentes desde la plataforma de gestión académica WebColegios hacia una base de datos PostgreSQL local.

El sistema resuelve eficientemente la necesidad de mantener actualizada la información institucional, utilizando Playwright Chromium para evadir protecciones, extraer reportes PDF/HTML y enriquecerlos, además de ofrecer una API web (FastAPI) y un panel interactivo (React) para realizar cargas manuales tolerantes a fallos.

## Arquitectura

```
Frontend React (Vite)
        │ HTTP
        ▼
  FastAPI (app.py)
   │          │
   │          ▼
   │    PostgreSQL (paz_y_salvo)
   │    ├── estudiantes
   │    ├── docentes
   │    ├── grados / jornadas
   │    ├── asignaciones
   │    ├── grupos
   │    ├── login
   │    └── bot_ejecuciones
   │
   ▼
main.py (scraping pipeline)
   ├── autenticacion.py  (Playwright)
   ├── navegacion.py     (Playwright)
   └── extraccion.py     (pdfplumber / HTML)
```

## Requisitos

- **Python** >= 3.10
- **PostgreSQL** >= 13
- **Node.js** >= 18

## Instalación desde cero

```bash
# 1. Clonar y crear entorno virtual
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Instalar dependencias Python
pip install -r requirements.txt

# 3. Instalar Chromium para Playwright
playwright install chromium

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con los valores reales

# 5. Inicializar base de datos
python setup_db.py

# 6. Registrar credenciales de scraping
python setup_login.py

# 7. Compilar el frontend
cd frontend && npm install && npm run build && cd ..

# 8. Iniciar el servidor
uvicorn app:app --host 0.0.0.0 --port 8000
# o en Windows: ejecutar.bat
```

## Variables de entorno

| Variable | Obligatoria | Descripción | Ejemplo |
|---|---|---|---|
| `DB_HOST` | Sí | Host de PostgreSQL | `localhost` |
| `DB_PORT` | Sí | Puerto de PostgreSQL | `5432` |
| `DB_NAME` | Sí | Nombre de la BD | `paz_y_salvo` |
| `DB_USER` | Sí | Usuario de la BD | `postgres` |
| `DB_PASSWORD` | Sí | Contraseña de PostgreSQL | `supersecreto` |
| `ENCRYPTION_KEY` | Sí | Clave base64 Fernet para encriptar la tabla de login | `(clave base64 de 32 bytes)` |
| `API_KEY` | Sí | Token para acceder a los endpoints protegidos | `mi_secreto_api_123` |
| `WEB_URL` | No | URL de la institución WebColegios | `https://www.webcolegios.com/demo/` |
| `WEB_TIPO_USUARIO` | No | Rol del portal web | `Administrativo` |
| `HEADLESS` | No | Modo sin interfaz gráfica Playwright | `True` |
| `PAGE_TIMEOUT` | No | Tiempo máximo de carga de páginas | `30` |
| `ELEMENT_TIMEOUT` | No | Tiempo máximo esperando un elemento | `20` |
| `DOWNLOAD_TIMEOUT` | No | Tiempo máximo para descargas | `60` |
| `GRADO_ID_DEFAULT` | No | Grado a asignar en caso de fallos | `1` |
| `LOG_LEVEL` | No | Nivel de logging | `INFO` |

## Endpoints principales

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `GET` | `/` | No | Retorna la aplicación React compilada |
| `GET` | `/api/health` | No | Monitorea la salud del servidor y la base de datos |
| `GET` | `/api/status` | No | Devuelve la ejecución de scraping activa actual si existe |
| `POST` | `/api/scrape/{tipo}` | Sí (API_KEY) | Inicia un proceso de scraping en segundo plano (`estudiantes`/`docentes`) |
| `POST` | `/api/import/manual` | Sí (API_KEY) | Inserta o actualiza un registro individual validado |
| `POST` | `/api/import/bulk` | Sí (API_KEY) | Importa un lote de registros aplicando savepoints para transaccionalidad |
| `GET` | `/api/logs` | No | Retorna logs usando lectura asíncrona por byte-offset (para el UI en tiempo real) |
| `GET` | `/api/ejecuciones` | No | Retorna el historial paginado de ejecuciones del bot |

## Troubleshooting

**Problema:** El dashboard muestra "scraping en ejecución" pero el proceso no está corriendo.

**Causa:** La aplicación se reinició de manera forzosa durante un scraping activo.

**Solución:** Al reiniciar de manera regular, el lifespan de FastAPI ejecuta automáticamente `marcar_ejecuciones_interrumpidas()` que cierra las ejecuciones huérfanas. Si el problema persiste sin reiniciar el proceso principal, puedes recuperar el estado manualmente ejecutando:
```bash
psql -U postgres -d paz_y_salvo -c "UPDATE bot_ejecuciones SET estado='interrumpido', fecha_fin=NOW() WHERE fecha_fin IS NULL;"
```

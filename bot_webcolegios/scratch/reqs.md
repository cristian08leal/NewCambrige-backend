



ESPECIFICACIÓN DE REQUERIMIENTOS

webcolegios_bot

Módulo de Poblar Base de Datos — Sistema Paz y Salvo Escolar







1. Contexto y alcance del módulo
El módulo webcolegios_bot es una herramienta de automatización cuya función principal es poblar la base de datos del sistema Paz y Salvo Escolar mediante tres mecanismos complementarios:

Scraping web automatizado sobre la plataforma WebColegios usando Playwright.
Importación manual de registros individuales a través del dashboard React.
Importación masiva desde archivos Excel/CSV con validación previa de datos.

El presente documento especifica los requerimientos formales y ejecutables que debe cumplir el módulo para considerarse operativamente estable, seguro y escalable. Cada requerimiento ha sido derivado del análisis exhaustivo del código fuente, incluyendo app.py, modules/database.py (839 líneas), modules/autenticacion.py, config/settings.py y la estructura SQL en sql/setup.sql.


2. Inventario de deuda técnica identificada
Los siguientes hallazgos constituyen los puntos de partida para la generación de requerimientos. Se clasifican por área y nivel de riesgo operativo.


Las credenciales de la plataforma WebColegios (usuario, contraseña) y de PostgreSQL (host, usuario, contraseña) están escritas en texto plano en config/settings.py. El archivo ha sido distribuido en el paquete del proyecto.
No existe tabla de autenticación de scraping en la base de datos. Los perfiles de acceso a WebColegios son globales y no trazables por ejecución.
El endpoint /api/scrape/{tipo} no requiere autenticación alguna. Cualquier proceso que acceda al puerto 8000 puede disparar un scraping completo.
Las variables de entorno están previstas en requirements.txt (python-dotenv) pero no se usan: settings.py ignora el .env y asigna valores hardcoded como fallback real, no como fallback de emergencia.


Sin pool de conexiones: cada función de database.py abre y cierra su propia conexión. En una importación masiva de 500 registros se generan entre 500 y 1.000 ciclos de conexión, consumiendo sockets y tiempo de autenticación innecesariamente.
Diseño partido entre grado_id (FK hacia tabla grados) y grado_texto (VARCHAR libre). En la práctica todos los insertos usan GRADO_ID_DEFAULT = 1 y el texto real vive en grado_texto sin constraint. La FK existe pero no aporta integridad real.
La columna jornada en estudiantes es un VARCHAR libre validado solo por lista Python (JORNADAS_VALIDAS). Si se añade una jornada nueva en el futuro, el cambio debe hacerse en código, no en datos.
La relación docente-titular de estudiantes se implementa mediante un trigger fn_sync_titular_estudiantes que actualiza el campo titular de la tabla estudiantes cuando se modifica un docente. Esto crea lógica de negocio implícita y difícil de auditar.
La tabla grupos no tiene FK hacia grados, permitiendo inconsistencias de texto (tilde vs sin tilde).
El DDL de creación de tablas (asegurar_tablas_docentes, asegurar_codigo_interno_estudiantes) se ejecuta en cada operación de escritura como bloque DO $$ en tiempo de transacción, añadiendo latencia y ruido a los logs.


procesar_importacion_masiva detiene todo el lote y hace rollback ante el primer registro inválido. Registros válidos previos también se pierden. El operador debe corregir y subir el archivo completo de nuevo.
La lista GRADOS_VALIDOS y JORNADAS_VALIDAS está duplicada en insertar_o_actualizar_persona y en procesar_importacion_masiva. Un cambio de grados debe actualizarse en dos lugares.
verificar_duplicado abre su propia conexión independiente aunque se llame inmediatamente antes de insertar_o_actualizar_persona, duplicando el overhead de conexión en el flujo manual del dashboard.
insertar_estudiantes (scraping) y el módulo de importación manual siguen lógicas diferentes de inserción: la primera usa un mapa de titulares cargado en memoria; la segunda no. Un estudiante importado manualmente nunca tendrá titular asignado hasta que corra el trigger.


El estado del scraping (scrape_status) vive como diccionario en memoria de la aplicación. Un reinicio del servidor deja el estado corrupto como running: True sin forma de recuperarse excepto reiniciando manualmente.
bot_ejecuciones no tiene columna login_id. No es posible saber qué perfil de acceso ejecutó cada sesión de scraping.
El endpoint /api/logs lee el archivo bot.log completo en cada llamada. Con logs de varios días acumulados, esto puede volverse lento. El endpoint acepta un parámetro line pero carga todo el archivo en memoria antes de hacer el slice.
No existe endpoint de health-check que verifique conectividad a la base de datos antes de responder. El dashboard puede mostrar datos vacíos sin indicar que hay un problema de conexión.


El directorio node_modules del frontend fue incluido en el paquete zip del proyecto, inflando el archivo a 146 MB. El .gitignore del frontend existe pero no se aplicó al momento de empaquetar.
El proyecto usa dos motores de automatización web simultáneamente: Playwright (en autenticacion.py y la mayor parte del scraping) y referencias a Selenium (driver_setup.py importa de modules que a su vez referencia Selenium). Esto genera dependencias duplicadas.
requirements.txt incluye Pillow como dependencia opcional pero no hay código que la use en producción. pandas está listado pero el scraping principal no lo usa directamente en el pipeline de datos.


3. Especificación de requerimientos
Los requerimientos se organizan en seis dominios. Cada uno incluye una tabla de requerimientos con identificador único, prioridad, descripción ejecutable, categoría y tipo (funcional o no funcional). El criterio de prioridad es:

CRÍTICA — Bloquea la operación segura. Debe resolverse antes de cualquier despliegue en producción.
ALTA — Genera pérdida de recursos o inconsistencia de datos. Debe resolverse en el primer sprint post-análisis.
MEDIA — Afecta la mantenibilidad y experiencia del operador. Resolver en sprint 2.
BAJA — Mejora de higiene técnica. Resolver en sprint 3 o al abordar la zona relacionada.

3.1  Dominio SEG — Seguridad y credenciales

3.2  Dominio BD — Base de datos y esquema


3.3  Dominio COD — Código y arquitectura de módulos

3.4  Dominio API — Endpoints y contrato HTTP


3.5  Dominio OPS — Operabilidad y trazabilidad

3.6  Dominio FE — Frontend y empaquetado


4. Mapa de prioridades y secuencia de ejecución
La siguiente secuencia de ejecución es la recomendada para no generar regresiones. Los requerimientos críticos deben resolverse antes de cualquier despliegue productivo. Los de alta prioridad conforman el Sprint 1 post-análisis.



5. Criterios de aceptación globales
Un requerimiento se considera CERRADO cuando cumple todos los criterios de aceptación aplicables a su dominio. A continuación se listan los criterios transversales que aplican a cualquier requerimiento, más los específicos por dominio.

5.1  Criterios transversales (aplican a todos los requerimientos)
El cambio no introduce regresiones en los tests existentes ni en los flujos de scraping ya funcionales.
El cambio no requiere modificar manualmente la base de datos de producción fuera de las migraciones provistas.
El código modificado pasa flake8 (PEP 8) sin errores nuevos.
Los logs del servidor no muestran errores ni warnings no esperados después del cambio.

5.2  Criterios específicos por dominio
SEG: Al ejecutar grep -r 'password\|contraseña\|WEB_PASSWORD' config/ sobre el repositorio versionado, el resultado debe estar vacío. La tabla login debe existir y tener al menos un registro de perfil de acceso funcional antes de ejecutar el primer scraping.
BD: Una importación masiva de 500 registros no debe generar más de 12 conexiones concurrentes al pool. El tiempo de inserción de 500 registros debe ser inferior a 8 segundos en entorno local con PostgreSQL en localhost.
COD: procesar_importacion_masiva con un lote de 100 registros donde 10 son inválidos debe retornar total_ok=90, total_rechazados=10 y hacer commit de los 90 válidos, sin revertir el lote completo.
API: GET /api/health debe responder en menos de 3 segundos en cualquier condición de red normal. Si la BD está caída, debe responder HTTP 503 con { db: 'error' } en menos de 5 segundos (tiempo de timeout del check).
OPS: Un reinicio del servidor uvicorn mientras hay un scraping en curso debe registrar el estado de esa ejecución como 'interrumpido' en bot_ejecuciones al reiniciar, no dejarla como 'iniciado' indefinidamente.
FE: El directorio node_modules no debe aparecer en el listado git status después de un git clone limpio del repositorio. npm run build en la carpeta frontend debe completarse sin errores.


6. Resumen ejecutivo


Total de requerimientos: 38. De los cuales 6 son de prioridad CRÍTICA y deben resolverse inmediatamente antes de cualquier uso en entorno de producción.

La deuda técnica más costosa operativamente no es la falta de funcionalidades sino la combinación de credenciales en código fuente + ausencia de pool de conexiones + importación masiva que pierde trabajo válido ante errores parciales. Estas tres condiciones hacen el módulo inseguro, ineficiente y frustrante de operar, respectivamente. La buena noticia es que los tres tienen solución directa y bien acotada.


Documento generado por análisis de código fuente — webcolegios_bot v1.0 — Mayo 2026
Versión|1.0 — Línea base de mejora
Fecha|Mayo 2026
Clasificación|Confidencial — Uso interno
Rol revisor|Senior Architecture & Supervision
2.1  Seguridad  —  Riesgo CRÍTICO
2.2  Base de datos  —  Riesgo ALTO
2.3  Lógica de negocio  —  Riesgo MEDIO
2.4  Operabilidad y trazabilidad  —  Riesgo MEDIO
2.5  Empaquetado y entorno  —  Riesgo BAJO
ID|Prioridad|Descripción del requerimiento|Categoría|Tipo
SEG-01|CRÍTICA|Eliminar todas las credenciales hardcodeadas de settings.py. El archivo debe leer cada valor exclusivamente desde variables de entorno (.env) sin fallback a valores literales. Los valores por defecto permitidos son solo estructurales (host localhost, puerto 5432), nunca contraseñas ni usuarios.|Seguridad|NF
SEG-02|CRÍTICA|Crear un archivo .env.example versionado con todas las claves requeridas en blanco (DB_PASSWORD=, WEB_PASSWORD=). El .env real debe listarse en .gitignore y en el .dockerignore si aplica.|Seguridad|NF
SEG-03|CRÍTICA|Crear la tabla login en PostgreSQL con los campos: id, url_plataforma, usuario, password_enc (cifrado AES-256 o Fernet), tipo_usuario, activo, created_at, updated_at. El campo password_enc almacena la contraseña cifrada con clave maestra tomada de variable de entorno ENCRYPTION_KEY.|BD / Seguridad|F
SEG-04|CRÍTICA|La función get_credentials_scraping() en database.py debe obtener las credenciales de la tabla login en lugar de importarlas de settings.py. El módulo autenticacion.py recibe las credenciales como parámetros, no como importaciones globales.|Seguridad|F
SEG-05|ALTA|Agregar autenticación básica (API key en header X-API-Key o JWT) a los endpoints POST /api/scrape/{tipo}, POST /api/import/manual y POST /api/import/bulk. Requests sin header válido deben recibir HTTP 401.|Seguridad|F
SEG-06|ALTA|La columna login_id debe agregarse a la tabla bot_ejecuciones como FK nullable hacia login.id. Cada sesión de scraping debe registrar el ID del perfil que la ejecutó.|BD / Trazabilidad|F
ID|Prioridad|Descripción del requerimiento|Categoría|Tipo
BD-01|CRÍTICA|Implementar pool de conexiones PostgreSQL al inicio de la aplicación usando psycopg2.pool.ThreadedConnectionPool(minconn=2, maxconn=10). Todas las funciones de database.py deben obtener conexiones del pool (getconn) y devolverlas (putconn) en el bloque finally. Prohibir la creación de conexiones ad-hoc con get_connection() fuera del arranque del pool.|BD / Rendimiento|NF
BD-02|ALTA|Crear la tabla jornadas como catálogo: id SERIAL PK, nombre VARCHAR(50) UNIQUE, activo BOOLEAN DEFAULT TRUE. Insertar los valores 'Completa', 'Continua', 'Nocturna' en la migración inicial. Cambiar la columna jornada de estudiantes a jornada_id INT FK hacia jornadas.|BD / Normalización|F
BD-03|ALTA|Unificar el campo de grado en estudiantes: eliminar grado_texto y usar exclusivamente grado_id como FK hacia la tabla grados. La tabla grados debe tener un campo nombre UNIQUE para hacer JOINs por nombre cuando lleguen datos del scraper como texto. Proveer función auxiliar grado_id_from_nombre(nombre) que devuelve el ID o inserta el grado si no existe.|BD / Normalización|F
BD-04|ALTA|Agregar FK desde grupos.grado hacia grados.nombre o reemplazar el campo texto por grupos.grado_id FK hacia grados. Asegurar que la comparación grado en grupos y grado_texto en estudiantes use el mismo identificador para eliminar errores de tilde/mayúsculas.|BD / Integridad|F
BD-05|ALTA|Eliminar el trigger fn_sync_titular_estudiantes y la lógica que lo crea en _asegurar_trigger_titular. Crear la tabla asignaciones: id SERIAL PK, docente_id INT FK, grado_id INT FK, curso VARCHAR(10), vigente BOOLEAN DEFAULT TRUE, created_at TIMESTAMP. La vista o consulta para obtener el titular de un grupo debe hacer JOIN con esta tabla en tiempo de lectura, no mediante campo desnormalizado.|BD / Arquitectura|F
BD-06|MEDIA|Mover todo el DDL de creación y verificación de tablas (asegurar_tablas_docentes, asegurar_codigo_interno_estudiantes, asegurar_tabla_grupos, asegurar_grado_default) a un script de inicialización único db_init.py que se ejecuta una sola vez al arrancar la aplicación con lifespan de FastAPI. Prohibir que las funciones de inserción llamen a DDL en cada transacción.|BD / Rendimiento|NF
BD-07|MEDIA|Agregar los índices faltantes: INDEX ON estudiantes(grado_id, curso) para búsquedas por grupo, INDEX ON docentes(grado_id) para búsquedas de titular, INDEX ON bot_ejecuciones(fecha_inicio DESC) para consultas del dashboard de trazabilidad.|BD / Rendimiento|NF
BD-08|BAJA|Agregar columnas de auditoría updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP a estudiantes y docentes, con trigger de actualización automática ON UPDATE. Permite detectar cuándo fue la última sincronización de cada registro.|BD / Trazabilidad|F
ID|Prioridad|Descripción del requerimiento|Categoría|Tipo
COD-01|ALTA|Dividir modules/database.py (839 líneas) en al menos cuatro módulos: db_pool.py (gestión del pool), db_estudiantes.py (operaciones sobre estudiantes), db_docentes.py (operaciones sobre docentes), db_ejecuciones.py (trazabilidad). El módulo database.py puede mantenerse como fachada que re-exporta las funciones públicas para compatibilidad.|Arquitectura|NF
COD-02|ALTA|Extraer GRADOS_VALIDOS y JORNADAS_VALIDAS a un único módulo de configuración de dominio (constants.py o consultarlos desde la base de datos en arranque). Eliminar las listas duplicadas en insertar_o_actualizar_persona y procesar_importacion_masiva.|Mantenibilidad|NF
COD-03|ALTA|Cambiar el comportamiento de procesar_importacion_masiva a modo tolerante a fallos: procesar todos los registros del lote, coleccionar filas inválidas en un log de errores, y hacer commit de los registros válidos al final. Retornar siempre { status, total_procesados, total_ok, total_rechazados, log }. El rollback total solo debe ocurrir si hay un error de base de datos inesperado, no por validación de campos.|Lógica de negocio|F
COD-04|MEDIA|Eliminar la dependencia duplicada de motores de automatización. Consolidar en Playwright únicamente. Revisar modules/driver_setup.py y eliminar referencias a Selenium si no hay rutas que lo requieran. Remover selenium de requirements.txt si aplica.|Dependencias|NF
COD-05|MEDIA|Reescribir verificar_duplicado para que use la conexión del pool en lugar de abrir una conexión propia. Cuando se llame desde insertar_o_actualizar_persona, la verificación debe ocurrir dentro de la misma transacción, evitando una segunda apertura de conexión.|Rendimiento|NF
COD-06|MEDIA|Agregar type hints completos a todas las funciones públicas de database.py. Añadir docstrings con descripción, parámetros, retorno y excepciones posibles. El módulo debe ser legible sin necesidad de revisar el SQL embebido.|Mantenibilidad|NF
COD-07|BAJA|Limpiar requirements.txt: documentar cada dependencia con su justificación. Remover Pillow si no hay uso activo en producción. Consolidar la versión mínima de Python requerida (actualmente hay bytecode de CPython 3.11 y 3.14 en el zip).|Dependencias|NF
ID|Prioridad|Descripción del requerimiento|Categoría|Tipo
API-01|CRÍTICA|Reemplazar el diccionario en memoria scrape_status por consultas a la tabla bot_ejecuciones. El endpoint GET /api/status debe responder con el estado del último registro de bot_ejecuciones donde fecha_fin IS NULL, considerado 'en ejecución'. Un reinicio del servidor no debe dejar estado corrupto.|API / Estado|F
API-02|ALTA|Agregar endpoint GET /api/health que responda { db: 'ok'|'error', scraping_engine: 'ok'|'unavailable', version: string, uptime_seconds: int }. El check de base de datos debe ejecutar SELECT 1 con timeout de 2 segundos. HTTP 200 si todos los checks pasan, HTTP 503 si alguno falla.|API / Operabilidad|F
API-03|ALTA|El endpoint GET /api/logs debe leer el archivo usando seek al byte correspondiente a la línea solicitada, no cargando el archivo completo en memoria. Alternativamente, migrar los logs a una tabla PostgreSQL log_entries para consultas eficientes con LIMIT/OFFSET.|API / Rendimiento|NF
API-04|MEDIA|Agregar endpoint GET /api/ejecuciones que retorne el historial de bot_ejecuciones con paginación (limit, offset) y filtro por tipo (estudiantes/docentes) y estado. Esto permite al operador auditar el historial de sincronizaciones desde el dashboard sin acceder directamente a la base de datos.|API / Trazabilidad|F
API-05|MEDIA|Agregar validación de entrada con Pydantic a todos los endpoints que aceptan JSON. Los campos tipo, nombre, documento y grado deben tener validators que saniticen espacios extra y rechacen valores vacíos con mensajes de error descriptivos en español.|API / Calidad|NF
API-06|BAJA|Documentar todos los endpoints en el esquema OpenAPI de FastAPI usando el parámetro description en cada operación y ejemplos de request/response con example= en los campos Pydantic. La URL /docs debe ser el manual operativo del API.|API / Documentación|NF
ID|Prioridad|Descripción del requerimiento|Categoría|Tipo
OPS-01|ALTA|Agregar manejo de señales de proceso (SIGTERM, SIGINT) en app.py para que el servidor cierre el pool de conexiones limpiamente antes de salir. Usar el lifespan de FastAPI (async context manager) para init y teardown del pool.|Operabilidad|NF
OPS-02|ALTA|Configurar rotación automática de logs usando RotatingFileHandler o TimedRotatingFileHandler en lugar de FileHandler plano. Mantener máximo 7 archivos diarios de log. El archivo bot.log actual crece indefinidamente.|Operabilidad|NF
OPS-03|MEDIA|Crear un script de setup inicial setup_db.py que ejecute en orden: creación de tablas, inserción de catálogos (grados, jornadas, grupos), y verificación de constraints. El script debe ser idempotente y reportar qué cambios aplicó. Reemplaza la ejecución manual de sql/setup.sql.|Operabilidad|F
OPS-04|MEDIA|Generar un archivo ejecutar.bat (Windows) y ejecutar.sh (Linux/Mac) que active el entorno virtual si existe, verifique las variables de entorno requeridas, ejecute setup_db.py y luego inicie uvicorn. El operador no debe necesitar conocer la secuencia de comandos.|Operabilidad|F
OPS-05|MEDIA|Implementar un mecanismo de retry con backoff exponencial en autenticacion.py para los casos en que el captcha falla o el elemento de login no carga. Actualmente un fallo en este punto termina todo el proceso sin reintento.|Resiliencia|F
OPS-06|BAJA|Agregar al README.md un diagrama ASCII o referencia al diagrama de arquitectura, la secuencia de comandos completa de instalación en entorno limpio, descripción de cada variable de entorno, y procedimiento de recuperación ante estado de scraping corrupto.|Documentación|NF
ID|Prioridad|Descripción del requerimiento|Categoría|Tipo
FE-01|ALTA|Agregar node_modules al .gitignore raíz del proyecto y al .gitignore de la carpeta frontend. Verificar que el proceso de build genera static_react/ correctamente antes de cada despliegue ejecutando npm run build desde la carpeta frontend.|Empaquetado|NF
FE-02|MEDIA|Implementar un indicador visual de estado de conexión en el dashboard React que llame a GET /api/health cada 30 segundos. Si la BD o el scraping engine no responden, mostrar un banner de advertencia en lugar de datos vacíos silenciosos.|UX / Operabilidad|F
FE-03|MEDIA|El componente MassImport.jsx debe mostrar al finalizar la importación una tabla de resultados con tres secciones: registros admitidos, registros actualizados y filas rechazadas con la razón de rechazo. Actualmente solo muestra un contador total.|UX / Funcional|F
FE-04|BAJA|Reemplazar el uso de react-icons (que importa el paquete completo con todos los icon sets) por imports específicos del icon set usado, o migrar a un set más liviano como @tabler/icons-react. El bundle actual incluye todos los icon families sin tree-shaking efectivo.|Rendimiento FE|NF
Fase|Requerimientos|Objetivo de la fase
Fase 0 — Urgente|SEG-01, SEG-02, SEG-03, SEG-04, API-01|Sacar las credenciales del código. Crear tabla login. Que el estado del scraping sea persistente. Sin esto el módulo no debería usarse en producción.
Fase 1 — Sprint 1|BD-01, BD-02, BD-03, BD-04, BD-05, SEG-05, SEG-06, COD-01, COD-02, COD-03, API-02|Pool de conexiones, normalización del esquema, eliminar trigger, dividir database.py, importación masiva tolerante a fallos, autenticación de endpoints, health-check.
Fase 2 — Sprint 2|BD-06, BD-07, COD-04, COD-05, COD-06, API-03, API-04, API-05, OPS-01, OPS-02, OPS-03, OPS-04, OPS-05, FE-01, FE-02, FE-03|DDL al arranque, índices adicionales, eliminar Selenium duplicado, logs eficientes, historial de ejecuciones, validaciones Pydantic, scripts de setup, retry en autenticación, indicador de salud en dashboard, resultados de importación masiva.
Fase 3 — Sprint 3|BD-08, COD-07, API-06, OPS-06, FE-04|Auditoría de updated_at, limpieza de requirements, documentación OpenAPI, README actualizado, optimización de bundle del frontend.
Dominio|Críticos|Altos|Medios|Bajos
SEG — Seguridad|4|2|0|0
BD — Base de datos|1|4|2|1
COD — Código|0|3|3|1
API — Endpoints|1|2|2|1
OPS — Operabilidad|0|2|4|1
FE — Frontend|0|1|2|1
TOTAL|6|14|13|5

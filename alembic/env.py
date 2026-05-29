import sys
import os

# Forzar UTF-8 en Windows para rutas con caracteres especiales (ñ, á, etc.)
# Esto debe ir ANTES de cualquier otro import que use la base de datos
os.environ["PYTHONUTF8"] = "1"
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from logging.config import fileConfig
from sqlalchemy import pool, create_engine
from alembic import context
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Importar Base y TODOS los modelos para que Alembic los detecte
from app.core.database import Base

# ── Importa cada módulo que tenga models.py ──────────────────────────────
import app.modules.usuarios.models      # noqa: F401
import app.modules.auth.models          # noqa: F401
import app.shared.models                # noqa: F401
import app.modules.paz_y_salvo.models    # noqa: F401
import app.modules.salon.models         # noqa: F401
import app.modules.estudiantes.models   # noqa: F401
import app.modules.banda.models         # noqa: F401
import app.modules.tesoreria.models     # noqa: F401
import app.modules.uniformes.models     # noqa: F401
import app.modules.rectoria.models      # noqa: F401
import app.modules.secretaria.models    # noqa: F401


# Configuración de logging de alembic.ini
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Apuntar a la metadata de todos los modelos
target_metadata = Base.metadata

# Inyectar la URL desde la variable de entorno
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Usamos create_engine directamente con la URL del entorno
    # para evitar problemas con rutas que contienen caracteres especiales (ñ)
    db_url = os.environ["DATABASE_URL"]
    connectable = create_engine(db_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

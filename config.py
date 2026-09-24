import os
from dotenv import load_dotenv

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Cargar variables del archivo .env
load_dotenv()

def _sanitize_db_url(url: str) -> str:
    if not url:
        return "postgresql://postgres:postgres@localhost:5432/polizas_db"
    
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    
    # Manejar query params no soportados directamente por libpq / psycopg2 (como pgbouncer=true de Neon/Prisma)
    try:
        parsed = urlparse(url)
        if parsed.query:
            query_params = parse_qs(parsed.query, keep_blank_values=True)
            # Eliminar pgbouncer si está presente
            query_params.pop("pgbouncer", None)
            # Reconstruir query
            clean_query = urlencode([(k, v) for k, values in query_params.items() for v in values])
            parsed = parsed._replace(query=clean_query)
            url = urlunparse(parsed)
    except Exception:
        pass
    return url

class Config:
    SQLALCHEMY_DATABASE_URI = _sanitize_db_url(os.getenv("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-12345")

    # Configuración JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

    # Configuración del Servicio de Auditoría
    AUDITORIA_SERVICE_URL = os.getenv("AUDITORIA_SERVICE_URL", "http://localhost:5001/api/auditoria/verificar-integridad")
    AUDITORIA_TIMEOUT = float(os.getenv("AUDITORIA_TIMEOUT", "5.0"))


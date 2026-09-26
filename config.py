import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Cargar variables del archivo .env si existe
load_dotenv()

DEFAULT_DB_URL = "postgresql://postgres.pkphvsmyohumvhaxgvmt:Grupo8.2026@aws-0-us-west-2.pooler.supabase.com:6543/postgres?pgbouncer=true"

def _get_env_str(key: str, default: str, fallback_key: str = None) -> str:
    val = os.getenv(key)
    if (val is None or not val.strip()) and fallback_key:
        val = os.getenv(fallback_key)
    if val is None or not val.strip():
        return default
    return val.strip()

def _get_env_float(key: str, default: float, fallback_key: str = None) -> float:
    val = os.getenv(key)
    if (val is None or not val.strip()) and fallback_key:
        val = os.getenv(fallback_key)
    if val is None or not val.strip():
        return default
    try:
        return float(val.strip())
    except (ValueError, TypeError):
        return default

def _sanitize_db_url(url: str) -> str:
    if not url or not str(url).strip():
        url = DEFAULT_DB_URL
    
    url = str(url).strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    # Manejar query params no soportados directamente por libpq / psycopg2 (como pgbouncer=true de Neon/Prisma/Supabase)
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
    SQLALCHEMY_DATABASE_URI = _sanitize_db_url(_get_env_str("DATABASE_URL", DEFAULT_DB_URL))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    SECRET_KEY = _get_env_str("SECRET_KEY", "motor-polizas-secret-key-2026")

    # Configuración JWT
    JWT_SECRET_KEY = _get_env_str("JWT_SECRET_KEY", "motor_polizas_super_secret_jwt_key_2026_segura_32bytes")
    JWT_ALGORITHM = _get_env_str("JWT_ALGORITHM", "HS256")

    # 1. Servicio Central de Auditoría (poliza_seguridad)
    AUDIT_SERVICE_URL = _get_env_str("AUDIT_SERVICE_URL", "https://polizaseguridad.vercel.app").rstrip("/")
    AUDIT_API_KEY = _get_env_str("AUDIT_API_KEY", "poliza-seguridad", fallback_key="AUDIT_SERVICE_API_KEY")

    # 2. Motor de Fraude (motor_fraude)
    FRAUDE_SERVICE_URL = _get_env_str("FRAUDE_SERVICE_URL", "https://motorfraude.vercel.app").rstrip("/")
    FRAUDE_API_KEY = _get_env_str("FRAUDE_API_KEY", "YUrM-jzVd5c9P61aVz43om81Q9lZoEHIECN3DNjGSiM")

    # 3. Motor de Respuesta a Incidentes (motor_respuesta_incidentes)
    RESPUESTA_SERVICE_URL = _get_env_str("RESPUESTA_SERVICE_URL", "https://motorrespuestaincidentes.vercel.app").rstrip("/")
    RESPUESTA_API_KEY = _get_env_str("RESPUESTA_API_KEY", "kIRNafZBKQH1-kGeBKxNf6NuNqgKD_QisIqlWJEYwbk")

    # Timeout estándar para servicios de seguridad (10 segundos según arquitectura)
    SECURITY_TIMEOUT = _get_env_float("SECURITY_TIMEOUT", 10.0, fallback_key="AUDITORIA_TIMEOUT")

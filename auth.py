import functools
from flask import current_app, g, jsonify, request
import jwt

def decode_and_validate_jwt(token: str):
    """
    Decodifica y valida la firma, expiración y claims mínimos (codigo_usuario, rol) del token JWT.
    Retorna el payload decodificado si es válido, o levanta excepciones de jwt o ValueError.
    """
    secret_key = current_app.config.get("JWT_SECRET_KEY")
    algorithm = current_app.config.get("JWT_ALGORITHM", "HS256")

    # Validar firma y expiración
    payload = jwt.decode(token, secret_key, algorithms=[algorithm])

    # Validar presencia del código de usuario (acepta 'codigo_usuario' o 'sub' / 'user_id')
    codigo_usuario = payload.get("codigo_usuario") or payload.get("sub") or payload.get("user_id")
    if not codigo_usuario:
        raise ValueError("El token no contiene el claim de código de usuario ('codigo_usuario' o 'sub')")

    # Validar presencia del rol (acepta 'rol' o 'role')
    rol = payload.get("rol") or payload.get("role")
    if not rol:
        raise ValueError("El token no contiene el claim de rol ('rol' o 'role')")

    # Normalizar payload para fácil acceso
    payload["codigo_usuario"] = codigo_usuario
    payload["rol"] = rol

    return payload


def token_required(allowed_roles=None):
    """
    Decorador para proteger rutas con validación de JWT.
    Verifica:
    - Encabezado Authorization: Bearer <token>
    - Firma válida y vigencia del token
    - Presencia de 'codigo_usuario' y 'rol'
    - Permisos de rol si allowed_roles está definido (string o lista/tupla de strings)
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return jsonify({
                    "error": "No autorizado",
                    "mensaje": "Cabecera 'Authorization' faltante"
                }), 401

            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return jsonify({
                    "error": "No autorizado",
                    "mensaje": "Formato de token inválido. Debe ser: 'Bearer <token>'"
                }), 401

            token = parts[1]

            try:
                payload = decode_and_validate_jwt(token)
            except jwt.ExpiredSignatureError:
                return jsonify({
                    "error": "No autorizado",
                    "mensaje": "El token ha expirado"
                }), 401
            except jwt.InvalidSignatureError:
                return jsonify({
                    "error": "No autorizado",
                    "mensaje": "Firma del token inválida"
                }), 401
            except jwt.DecodeError:
                return jsonify({
                    "error": "No autorizado",
                    "mensaje": "Token JWT malformado o inválido"
                }), 401
            except ValueError as ve:
                return jsonify({
                    "error": "No autorizado",
                    "mensaje": str(ve)
                }), 401
            except Exception as e:
                return jsonify({
                    "error": "No autorizado",
                    "mensaje": f"Error al validar token: {str(e)}"
                }), 401

            # Validar autorización por rol si aplica
            if allowed_roles:
                user_role = payload.get("rol")
                if user_role not in allowed_roles:
                    return jsonify({
                        "error": "Acceso prohibido",
                        "mensaje": f"Rol '{user_role}' no autorizado para esta operación. Roles permitidos: {allowed_roles}"
                    }), 403

            # Almacenar el usuario actual en el contexto de la petición de Flask
            g.current_user = payload

            return fn(*args, **kwargs)
        return wrapper
    return decorator

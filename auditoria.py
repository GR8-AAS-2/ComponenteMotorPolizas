import requests
from flask import current_app, request, has_request_context


def obtener_ip_cliente():
    """
    Obtiene la IP de origen de la petición actual en Flask.
    Soporta cabeceras 'X-Forwarded-For' en caso de estar detrás de un proxy o balanceador.
    """
    if not has_request_context():
        return None
    try:
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.remote_addr
    except Exception:
        return None


def verificar_integridad_con_auditoria(datos_poliza, codigo_usuario=None, rol=None, ip_origen=None):
    """
    Envía los datos de la(s) póliza(s) al servicio de auditoría para validar su integridad contra un hash.

    Retorna:
        - (True, None, 200) si la auditoría confirma la integridad (flag == True).
        - (False, respuesta_auditoria, status_code) si la bandera es False o hay fallo.
    """
    url = current_app.config.get("AUDITORIA_SERVICE_URL")
    timeout = current_app.config.get("AUDITORIA_TIMEOUT", 5.0)

    if ip_origen is None:
        ip_origen = obtener_ip_cliente()

    payload = {
        "datos": datos_poliza,
        "codigo_usuario": codigo_usuario,
        "rol": rol,
        "ip_origen": ip_origen
    }

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        
        try:
            audit_data = response.json()
        except Exception:
            audit_data = {"mensaje": response.text, "status_code": response.status_code}

        # Comprobar la bandera en la respuesta de auditoría
        # Soporta claves estándar: 'flag', 'valido', 'aprobado', 'integridad_valida'
        flag = False
        if isinstance(audit_data, dict):
            if "flag" in audit_data:
                flag = bool(audit_data["flag"])
            elif "valido" in audit_data:
                flag = bool(audit_data["valido"])
            elif "aprobado" in audit_data:
                flag = bool(audit_data["aprobado"])
            elif "integridad_valida" in audit_data:
                flag = bool(audit_data["integridad_valida"])
            else:
                # Si no viene una clave específica pero el status fue 200, verificar status
                flag = response.status_code == 200

        if flag:
            return True, None, 200
        else:
            # Si el flag es False, devolvemos la respuesta emitida por auditoría
            status_code = response.status_code if response.status_code != 200 else 400
            return False, audit_data, status_code

    except requests.exceptions.Timeout:
        return False, {
            "error": "Timeout en servicio de auditoría",
            "mensaje": "El servicio de auditoría no respondió a tiempo",
            "flag": False
        }, 504
    except requests.exceptions.ConnectionError:
        return False, {
            "error": "Error de conexión con auditoría",
            "mensaje": "No fue posible conectar con el servicio de auditoría",
            "flag": False
        }, 503
    except Exception as e:
        return False, {
            "error": "Error inesperado al consultar auditoría",
            "mensaje": str(e),
            "flag": False
        }, 500


def auditar_usuario(codigo_usuario=None, rol=None, accion=None, ip_origen=None, detalles=None):
    """
    Envía únicamente la información del usuario e IP al servicio de auditoría (sin datos de pólizas).

    Retorna:
        - (True, respuesta_auditoria, status_code) si la auditoría confirma el registro exitoso.
        - (False, respuesta_auditoria, status_code) si hay fallo o error de conexión.
    """
    url = current_app.config.get("AUDITORIA_SERVICE_URL")
    timeout = current_app.config.get("AUDITORIA_TIMEOUT", 5.0)

    if ip_origen is None:
        ip_origen = obtener_ip_cliente()

    payload = {
        "codigo_usuario": codigo_usuario,
        "rol": rol,
        "ip_origen": ip_origen
    }
    if accion:
        payload["accion"] = accion
    if detalles is not None:
        payload["detalles"] = detalles

    try:
        response = requests.post(url, json=payload, timeout=timeout)

        try:
            audit_data = response.json()
        except Exception:
            audit_data = {"mensaje": response.text, "status_code": response.status_code}

        is_success = response.status_code in (200, 201)
        if isinstance(audit_data, dict) and "flag" in audit_data:
            is_success = bool(audit_data["flag"]) and is_success

        return is_success, audit_data, response.status_code

    except requests.exceptions.Timeout:
        return False, {
            "error": "Timeout en servicio de auditoría",
            "mensaje": "El servicio de auditoría no respondió a tiempo",
            "flag": False
        }, 504
    except requests.exceptions.ConnectionError:
        return False, {
            "error": "Error de conexión con auditoría",
            "mensaje": "No fue posible conectar con el servicio de auditoría",
            "flag": False
        }, 503
    except Exception as e:
        return False, {
            "error": "Error inesperado al consultar auditoría",
            "mensaje": str(e),
            "flag": False
        }, 500

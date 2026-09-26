import requests
from flask import current_app, request, has_request_context


def obtener_ip_cliente():
    """
    Obtiene la IP de origen de la petición actual en Flask.
    Soporta cabeceras 'X-Forwarded-For' en caso de estar detrás de un proxy, Vercel o balanceador.
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


def normalizar_8_campos_poliza(poliza_dict_o_obj):
    """
    Normaliza los 8 campos obligatorios que exige el Motor de Fraude:
    - numero_poliza (str)
    - tipo_documento (str)
    - documento_identidad (str)
    - ramo (str)
    - tipo_cobertura (str)
    - monto_asegurado (decimal en formato string con 2 decimales, ej: '85000000.00')
    - fecha_inicio_vigencia (YYYY-MM-DD)
    - fecha_fin_vigencia (YYYY-MM-DD)
    """
    if hasattr(poliza_dict_o_obj, "to_dict"):
        data = poliza_dict_o_obj.to_dict()
    elif isinstance(poliza_dict_o_obj, dict):
        data = poliza_dict_o_obj
    else:
        data = {}

    monto = data.get("monto_asegurado", 0.0)
    try:
        monto_str = f"{float(monto):.2f}"
    except (ValueError, TypeError):
        monto_str = "0.00"

    f_inicio = data.get("fecha_inicio_vigencia")
    f_inicio_str = f_inicio.isoformat() if hasattr(f_inicio, "isoformat") else str(f_inicio or "")

    f_fin = data.get("fecha_fin_vigencia")
    f_fin_str = f_fin.isoformat() if hasattr(f_fin, "isoformat") else str(f_fin or "")

    return {
        "numero_poliza": str(data.get("numero_poliza") or ""),
        "tipo_documento": str(data.get("tipo_documento") or "CC"),
        "documento_identidad": str(data.get("documento_identidad") or ""),
        "ramo": str(data.get("ramo") or ""),
        "tipo_cobertura": str(data.get("tipo_cobertura") or ""),
        "monto_asegurado": monto_str,
        "fecha_inicio_vigencia": f_inicio_str,
        "fecha_fin_vigencia": f_fin_str
    }


# ==============================================================================
# 1. SERVICIO CENTRAL DE AUDITORÍA (poliza_seguridad)
# ==============================================================================

def registrar_log_auditoria(tipo_evento, evento, identificador, detalle=None, usuario_id=None, ip_origen=None):
    """
    Registra un evento en audit_logs de la Auditoría Central (POST /api/logs).
    """
    base_url = current_app.config.get("AUDIT_SERVICE_URL", "https://polizaseguridad.vercel.app")
    api_key = current_app.config.get("AUDIT_API_KEY", "")
    timeout = current_app.config.get("SECURITY_TIMEOUT", 10.0)

    if ip_origen is None:
        ip_origen = obtener_ip_cliente()

    payload = {
        "tipo_evento": tipo_evento,
        "evento": evento,
        "identificador": identificador,
        "detalle": detalle or {},
        "usuario_id": usuario_id,
        "ip_origen": ip_origen
    }

    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        response = requests.post(f"{base_url}/api/logs", json=payload, headers=headers, timeout=timeout)
        try:
            return response.status_code in (200, 201), response.json(), response.status_code
        except Exception:
            return response.status_code in (200, 201), {"mensaje": response.text}, response.status_code
    except requests.exceptions.Timeout:
        return False, {"error": "Timeout en Servicio de Auditoría"}, 504
    except requests.exceptions.ConnectionError:
        return False, {"error": "Error de conexión con Servicio de Auditoría"}, 503
    except Exception as e:
        return False, {"error": f"Fallo al registrar log de auditoría: {str(e)}"}, 500


def consultar_actividad_usuario(usuario_id, tipo_evento="Seguridad", evento="New_Rol", limite_historial=100):
    """
    Consulta la IP habitual y última conexión de un usuario (GET /api/logs/actividad-usuario).
    """
    base_url = current_app.config.get("AUDIT_SERVICE_URL", "https://polizaseguridad.vercel.app")
    api_key = current_app.config.get("AUDIT_API_KEY", "")
    timeout = current_app.config.get("SECURITY_TIMEOUT", 10.0)

    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    params = {
        "usuario_id": usuario_id,
        "tipo_evento": tipo_evento,
        "evento": evento,
        "limite_historial": limite_historial
    }

    try:
        response = requests.get(f"{base_url}/api/logs/actividad-usuario", params=params, headers=headers, timeout=timeout)
        return response.status_code == 200, response.json(), response.status_code
    except Exception as e:
        return False, {"error": str(e)}, 500


# ==============================================================================
# 2. MOTOR DE FRAUDE (motor_fraude)
# ==============================================================================

def registrar_hash_poliza(poliza_dict_o_obj):
    """
    Registra el hash SHA-256 de una nueva póliza en el Motor de Fraude (POST /api/polizas/hash).
    """
    base_url = current_app.config.get("FRAUDE_SERVICE_URL", "https://motorfraude.vercel.app")
    api_key = current_app.config.get("FRAUDE_API_KEY", "")
    timeout = current_app.config.get("SECURITY_TIMEOUT", 10.0)

    payload = normalizar_8_campos_poliza(poliza_dict_o_obj)
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        response = requests.post(f"{base_url}/api/polizas/hash", json=payload, headers=headers, timeout=timeout)
        try:
            return response.status_code == 201, response.json(), response.status_code
        except Exception:
            return response.status_code == 201, {"mensaje": response.text}, response.status_code
    except Exception as e:
        return False, {"error": f"Fallo al registrar hash en Motor de Fraude: {str(e)}"}, 500


def validar_poliza_con_fraude(poliza_dict_o_obj):
    """
    Valida la integridad de una póliza contra el Motor de Fraude (POST /api/polizas/validar).
    
    Retorna:
    - (True, res_data, 200): si verificacion == 'directo' (hash coincide)
    - (True, res_data, 200): si verificacion == 'log_auditoria' (datos alterados pero recuperados de auditoría)
    - (False, res_data, 400/404): si verificacion == 'sin_confirmar' o 'sin_registro'
    """
    base_url = current_app.config.get("FRAUDE_SERVICE_URL", "https://motorfraude.vercel.app")
    api_key = current_app.config.get("FRAUDE_API_KEY", "")
    timeout = current_app.config.get("SECURITY_TIMEOUT", 10.0)

    payload = normalizar_8_campos_poliza(poliza_dict_o_obj)
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        response = requests.post(f"{base_url}/api/polizas/validar", json=payload, headers=headers, timeout=timeout)
        try:
            res_data = response.json()
        except Exception:
            res_data = {"mensaje": response.text, "status_code": response.status_code}

        verificacion = res_data.get("verificacion")
        hash_coincide = bool(res_data.get("hash_coincide"))

        # Caso 1: Integridad directa comprobada
        if verificacion == "directo" or (response.status_code == 200 and hash_coincide):
            return True, res_data, 200

        # Caso 2: Datos alterados en BD pero recuperados y confirmados desde log de auditoría
        if verificacion == "log_auditoria":
            return True, res_data, 200

        # Caso 3: Sin confirmar (posible alteración o fraude)
        if verificacion == "sin_confirmar":
            return False, res_data, 400

        # Caso 4: Póliza sin registro previo de hash
        if verificacion == "sin_registro" or response.status_code == 404:
            return False, res_data, 404

        # Fallback para respuestas genéricas
        return response.status_code == 200, res_data, response.status_code

    except requests.exceptions.Timeout:
        return False, {"error": "Timeout en Motor de Fraude", "mensaje": "El motor de fraude no respondió a tiempo"}, 504
    except requests.exceptions.ConnectionError:
        return False, {"error": "Error de conexión con Motor de Fraude", "mensaje": "No fue posible conectar con el motor de fraude"}, 503
    except Exception as e:
        return False, {"error": f"Fallo al validar póliza con Motor de Fraude: {str(e)}"}, 500


# ==============================================================================
# 3. MOTOR DE RESPUESTA A INCIDENTES (motor_respuesta_incidentes)
# ==============================================================================

def analizar_elevacion_privilegios(usuario_id, tipo_evento=None, evento=None, limite_historial=None):
    """
    Analiza si el usuario presenta elevación de privilegios desde una IP no habitual
    (POST /api/incidentes/elevacion-privilegios).
    """
    base_url = current_app.config.get("RESPUESTA_SERVICE_URL", "https://motorrespuestaincidentes.vercel.app")
    api_key = current_app.config.get("RESPUESTA_API_KEY", "")
    timeout = current_app.config.get("SECURITY_TIMEOUT", 10.0)

    payload = {
        "usuario_id": usuario_id
    }
    if tipo_evento:
        payload["tipo_evento"] = tipo_evento
    if evento:
        payload["evento"] = evento
    if limite_historial is not None:
        payload["limite_historial"] = int(limite_historial)

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        response = requests.post(f"{base_url}/api/incidentes/elevacion-privilegios", json=payload, headers=headers, timeout=timeout)
        try:
            res_data = response.json()
        except Exception:
            res_data = {"mensaje": response.text, "status_code": response.status_code}
        return response.status_code == 200, res_data, response.status_code
    except requests.exceptions.Timeout:
        return False, {"error": "Timeout en Motor de Incidentes", "mensaje": "El motor de incidentes no respondió a tiempo"}, 504
    except requests.exceptions.ConnectionError:
        return False, {"error": "Error de conexión con Motor de Incidentes", "mensaje": "No fue posible conectar con el motor de incidentes"}, 503
    except Exception as e:
        return False, {"error": f"Fallo en Motor de Incidentes: {str(e)}"}, 500


# ==============================================================================
# 4. FUNCIÓN INTEGRADA DE VALIDACIÓN DE INTEGRIDAD PARA ENDPOINTS GET
# ==============================================================================

def verificar_integridad_con_auditoria(datos_poliza, codigo_usuario=None, rol=None, ip_origen=None):
    """
    Valida la integridad de la(s) póliza(s) mediante el Motor de Fraude y registra
    el log de acceso en la Auditoría Central.

    Si datos_poliza es una lista, valida cada póliza o la primera y registra la consulta.
    Si se detecta alteración con recuperación ('log_auditoria'), sustituye los datos
    por los datos_correctos recuperados de auditoría.
    """
    if ip_origen is None:
        ip_origen = obtener_ip_cliente()

    # Si es una lista de pólizas
    if isinstance(datos_poliza, list):
        if not datos_poliza:
            # Registrar lectura vacía
            registrar_log_auditoria(
                tipo_evento="Poliza",
                evento="Read",
                identificador="TODAS",
                detalle={"total_consultadas": 0},
                usuario_id=codigo_usuario,
                ip_origen=ip_origen
            )
            return True, None, 200

        # Validar cada póliza de la lista con el motor de fraude
        polizas_validadas = []
        for p in datos_poliza:
            es_valido, res_fraude, status_code = validar_poliza_con_fraude(p)
            if not es_valido:
                # Registrar alerta en auditoría
                registrar_log_auditoria(
                    tipo_evento="Seguridad",
                    evento="Alerta_Integridad_Poliza",
                    identificador=p.get("numero_poliza", "DESCONOCIDO"),
                    detalle={"error_fraude": res_fraude, "rol": rol},
                    usuario_id=codigo_usuario,
                    ip_origen=ip_origen
                )
                return False, res_fraude, status_code

            # Si se recuperaron datos corregidos desde log_auditoria
            if res_fraude.get("verificacion") == "log_auditoria" and res_fraude.get("datos_correctos"):
                p_corregida = dict(p)
                p_corregida.update(res_fraude["datos_correctos"])
                polizas_validadas.append(p_corregida)
            else:
                polizas_validadas.append(p)

        # Registrar log de lectura exitosa
        registrar_log_auditoria(
            tipo_evento="Poliza",
            evento="Read",
            identificador="LISTADO_POLIZAS",
            detalle={"total_consultadas": len(datos_poliza)},
            usuario_id=codigo_usuario,
            ip_origen=ip_origen
        )

        return True, polizas_validadas, 200

    # Si es una sola póliza (diccionario)
    es_valido, res_fraude, status_code = validar_poliza_con_fraude(datos_poliza)
    numero_poliza = datos_poliza.get("numero_poliza", "DESCONOCIDO")

    if not es_valido:
        # Registrar alerta de integridad
        registrar_log_auditoria(
            tipo_evento="Seguridad",
            evento="Alerta_Integridad_Poliza",
            identificador=numero_poliza,
            detalle={"error_fraude": res_fraude, "rol": rol},
            usuario_id=codigo_usuario,
            ip_origen=ip_origen
        )
        return False, res_fraude, status_code

    # Log de lectura individual exitosa
    registrar_log_auditoria(
        tipo_evento="Poliza",
        evento="Read",
        identificador=numero_poliza,
        detalle={"verificacion": res_fraude.get("verificacion", "directo")},
        usuario_id=codigo_usuario,
        ip_origen=ip_origen
    )

    # Si se recuperaron datos corregidos desde auditoría
    if res_fraude.get("verificacion") == "log_auditoria" and res_fraude.get("datos_correctos"):
        datos_retorno = dict(datos_poliza)
        datos_retorno.update(res_fraude["datos_correctos"])
        return True, datos_retorno, 200

    return True, datos_poliza, 200

import os
from datetime import datetime
from flask import Flask, jsonify, request, g
from sqlalchemy import text
from config import Config
from models import db, Poliza
from auth import token_required
from auditoria import (
    verificar_integridad_con_auditoria,
    registrar_hash_poliza,
    registrar_log_auditoria,
    analizar_elevacion_privilegios,
    normalizar_8_campos_poliza,
    obtener_ip_cliente
)


def create_app(config_override=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if config_override:
        app.config.update(config_override)

    # Inicializar base de datos
    db.init_app(app)

    # Crear tablas automáticamente al iniciar si no existen
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"No se pudieron crear las tablas automáticamente al inicio: {e}")

    # ==========================
    # Rutas / Endpoints
    # ==========================

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "mensaje": "API Motor de Pólizas en Flask",
            "version": "1.0.0",
            "servicios_seguridad": {
                "auditoria_central": app.config.get("AUDIT_SERVICE_URL"),
                "motor_fraude": app.config.get("FRAUDE_SERVICE_URL"),
                "motor_incidentes": app.config.get("RESPUESTA_SERVICE_URL")
            },
            "endpoints": {
                "health": "/health",
                "polizas_get": "/api/polizas",
                "polizas_post": "/api/polizas",
                "incidentes_elevacion_privilegios": "/api/incidentes/elevacion-privilegios"
            }
        }), 200

    @app.route("/health", methods=["GET"])
    def health_check():
        """Verifica el estado del servicio y la conexión a PostgreSQL"""
        db_status = "desconectado"
        try:
            # Ejecutar consulta simple para probar la conexión
            db.session.execute(text("SELECT 1"))
            db_status = "conectado"
            return jsonify({
                "status": "ok",
                "database": db_status
            }), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "database": db_status,
                "error": str(e)
            }), 500

    @app.route("/api/polizas", methods=["GET"])
    @token_required()
    def get_polizas():
        """Obtener listado de pólizas (valida integridad contra Motor de Fraude y Auditoría)"""
        try:
            polizas = Poliza.query.all()
            datos_polizas = [p.to_dict() for p in polizas]

            # Validar integridad contra el ecosistema de seguridad (Motor de Fraude + Auditoría Central)
            es_valido, resultado, status_code = verificar_integridad_con_auditoria(
                datos_poliza=datos_polizas,
                codigo_usuario=g.current_user.get("codigo_usuario"),
                rol=g.current_user.get("rol")
            )

            # Si se detecta alteración no confirmada o fraude, retornar reporte de seguridad
            if not es_valido:
                return jsonify(resultado), status_code

            # Si es íntegro o los datos fueron recuperados de auditoría, entregar listado
            data_entregar = resultado if isinstance(resultado, list) else datos_polizas
            return jsonify({
                "usuario_autenticado": g.current_user.get("codigo_usuario"),
                "rol": g.current_user.get("rol"),
                "total": len(data_entregar),
                "data": data_entregar
            }), 200
        except Exception as e:
            return jsonify({"error": "Error al consultar pólizas", "detalle": str(e)}), 500

    @app.route("/api/polizas/<int:poliza_id>", methods=["GET"])
    @token_required()
    def get_poliza_by_id(poliza_id):
        """Obtener una póliza por ID (valida integridad contra Motor de Fraude y Auditoría)"""
        try:
            poliza = db.session.get(Poliza, poliza_id)
            if not poliza:
                return jsonify({"error": "Póliza no encontrada"}), 404

            datos_poliza = poliza.to_dict()

            # Validar integridad de la póliza
            es_valido, resultado, status_code = verificar_integridad_con_auditoria(
                datos_poliza=datos_poliza,
                codigo_usuario=g.current_user.get("codigo_usuario"),
                rol=g.current_user.get("rol")
            )

            # Si falla la validación de integridad
            if not es_valido:
                return jsonify(resultado), status_code

            # Retornar póliza íntegra o recuperada
            return jsonify(resultado if isinstance(resultado, dict) else datos_poliza), 200
        except Exception as e:
            return jsonify({"error": "Error al consultar la póliza", "detalle": str(e)}), 500

    @app.route("/api/polizas", methods=["POST"])
    @token_required()
    def create_poliza():
        """
        Crear una nueva póliza:
        1. Valida campos obligatorios.
        2. Registra el hash SHA-256 en el Motor de Fraude (POST /api/polizas/hash).
        3. Registra el log de creación en la Auditoría Central (POST /api/logs).
        4. Almacena la póliza en la base de datos PostgreSQL.
        """
        data = request.get_json()
        if not data:
            return jsonify({"error": "Cuerpo de solicitud JSON requerido"}), 400

        required_fields = [
            "numero_poliza", "titular", "documento_identidad",
            "ramo", "tipo_cobertura", "monto_asegurado",
            "fecha_inicio_vigencia", "fecha_fin_vigencia"
        ]
        missing = [f for f in required_fields if f not in data or data[f] is None or str(data[f]).strip() == ""]
        if missing:
            return jsonify({"error": f"Faltan campos obligatorios: {', '.join(missing)}"}), 400

        numero_poliza = str(data["numero_poliza"]).strip()

        # Verificar si ya existe en la base de datos local
        if Poliza.query.filter_by(numero_poliza=numero_poliza).first():
            return jsonify({"error": f"Ya existe una póliza con el número '{numero_poliza}' en el sistema"}), 409

        # 1. Registrar hash en el Motor de Fraude (POST /api/polizas/hash)
        es_valido_hash, res_hash, status_hash = registrar_hash_poliza(data)
        if not es_valido_hash:
            return jsonify({
                "error": "No se pudo registrar el hash en el Motor de Fraude",
                "detalle": res_hash
            }), status_hash

        # 2. Registrar log de creación en la Auditoría Central (POST /api/logs)
        campos_8 = normalizar_8_campos_poliza(data)
        ip_cliente = obtener_ip_cliente()
        registrar_log_auditoria(
            tipo_evento="Poliza",
            evento="Create",
            identificador=numero_poliza,
            detalle=campos_8,
            usuario_id=g.current_user.get("codigo_usuario"),
            ip_origen=ip_cliente
        )

        try:
            # Parsear fechas si vienen como string
            f_inicio = (
                datetime.strptime(data["fecha_inicio_vigencia"], "%Y-%m-%d").date()
                if isinstance(data["fecha_inicio_vigencia"], str)
                else data["fecha_inicio_vigencia"]
            )
            f_fin = (
                datetime.strptime(data["fecha_fin_vigencia"], "%Y-%m-%d").date()
                if isinstance(data["fecha_fin_vigencia"], str)
                else data["fecha_fin_vigencia"]
            )

            nueva_poliza = Poliza(
                numero_poliza=numero_poliza,
                titular=data["titular"],
                tipo_documento=data.get("tipo_documento", "CC"),
                documento_identidad=data["documento_identidad"],
                email_titular=data.get("email_titular"),
                telefono_titular=data.get("telefono_titular"),
                direccion=data.get("direccion"),
                ciudad=data.get("ciudad"),
                ramo=data["ramo"],
                tipo_cobertura=data["tipo_cobertura"],
                monto_asegurado=data["monto_asegurado"],
                prima_mensual=data.get("prima_mensual", 0.0),
                deducible=data.get("deducible", 0.0),
                fecha_inicio_vigencia=f_inicio,
                fecha_fin_vigencia=f_fin,
                frecuencia_pago=data.get("frecuencia_pago", "MENSUAL"),
                metodo_pago=data.get("metodo_pago", "DEBITO_AUTOMATICO"),
                estado=data.get("estado", "ACTIVA"),
                agente_codigo=data.get("agente_codigo"),
                agente_nombre=data.get("agente_nombre"),
                beneficiarios=data.get("beneficiarios")
            )
            db.session.add(nueva_poliza)
            db.session.commit()

            return jsonify({
                "mensaje": "Póliza creada exitosamente con hash registrado en Motor de Fraude",
                "creado_por": g.current_user.get("codigo_usuario"),
                "hash_seguridad": res_hash,
                "poliza": nueva_poliza.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al guardar la póliza en la base de datos", "detalle": str(e)}), 500

    @app.route("/api/incidentes/elevacion-privilegios", methods=["POST"])
    @token_required()
    def evaluar_elevacion_privilegios():
        """
        1. Registra el evento de cambio de rol en la Auditoría Central (POST https://polizaseguridad.vercel.app/api/logs).
        2. Analiza si el usuario presenta elevación de privilegios sospechosa
           consultando al Motor de Respuesta a Incidentes (POST https://motorrespuestaincidentes.vercel.app/api/incidentes/elevacion-privilegios).
        """
        data = request.get_json(silent=True) or {}
        usuario_id = data.get("usuario_id") or g.current_user.get("codigo_usuario")
        if not usuario_id:
            return jsonify({"error": "El campo 'usuario_id' es obligatorio"}), 400

        tipo_evento = data.get("tipo_evento", "Seguridad")
        evento = data.get("evento", "New_Rol")
        identificador = data.get("identificador") or f"cambio-rol-{int(datetime.utcnow().timestamp())}"
        ip_origen = data.get("ip_origen") or obtener_ip_cliente()

        detalle = data.get("detalle")
        if detalle is None:
            detalle = {
                "rol_anterior": data.get("rol_anterior", "consulta"),
                "rol_nuevo": data.get("rol_nuevo", "admin")
            }

        # 1. Registrar el evento de cambio de rol en la Auditoría Central
        registrar_log_auditoria(
            tipo_evento=tipo_evento,
            evento=evento,
            identificador=identificador,
            detalle=detalle,
            usuario_id=usuario_id,
            ip_origen=ip_origen
        )

        # 2. Consultar al Motor de Respuesta a Incidentes para evaluar si hubo vulneración
        es_exitoso, resultado_incidente, status_code = analizar_elevacion_privilegios(
            usuario_id=usuario_id,
            tipo_evento=tipo_evento if data.get("tipo_evento") else None,
            evento=evento if data.get("evento") else None,
            limite_historial=data.get("limite_historial")
        )

        return jsonify(resultado_incidente), status_code

    # ==========================
    # Manejadores de Error
    # ==========================
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Recurso no encontrado"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Error interno del servidor"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=port, debug=debug)

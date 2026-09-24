import os
from flask import Flask, jsonify, request, g
from sqlalchemy import text
from config import Config
from models import db, Poliza
from auth import token_required
from auditoria import verificar_integridad_con_auditoria


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
            "endpoints": {
                "health": "/health",
                "polizas": "/api/polizas"
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
        """Obtener listado de pólizas (valida integridad con auditoría antes de responder)"""
        try:
            polizas = Poliza.query.all()
            datos_polizas = [p.to_dict() for p in polizas]

            # Consultar al servicio de auditoría para validar integridad con hash
            es_valido, respuesta_auditoria, status_code = verificar_integridad_con_auditoria(
                datos_poliza=datos_polizas,
                codigo_usuario=g.current_user.get("codigo_usuario"),
                rol=g.current_user.get("rol")
            )

            # Si la bandera es False o falla la validación, retornar respuesta de auditoría
            if not es_valido:
                return jsonify(respuesta_auditoria), status_code

            # Si la bandera es True, retornar los datos normalmente
            return jsonify({
                "usuario_autenticado": g.current_user.get("codigo_usuario"),
                "rol": g.current_user.get("rol"),
                "data": datos_polizas
            }), 200
        except Exception as e:
            return jsonify({"error": "Error al consultar pólizas", "detalle": str(e)}), 500

    @app.route("/api/polizas/<int:poliza_id>", methods=["GET"])
    @token_required()
    def get_poliza_by_id(poliza_id):
        """Obtener una póliza por ID (valida integridad con auditoría antes de responder)"""
        try:
            poliza = db.session.get(Poliza, poliza_id)
            if not poliza:
                return jsonify({"error": "Póliza no encontrada"}), 404

            datos_poliza = poliza.to_dict()

            # Consultar al servicio de auditoría para validar integridad con hash
            es_valido, respuesta_auditoria, status_code = verificar_integridad_con_auditoria(
                datos_poliza=datos_poliza,
                codigo_usuario=g.current_user.get("codigo_usuario"),
                rol=g.current_user.get("rol")
            )

            # Si la bandera es False o falla la validación, retornar respuesta de auditoría
            if not es_valido:
                return jsonify(respuesta_auditoria), status_code

            # Si la bandera es True, retornar los datos normalmente
            return jsonify(datos_poliza), 200
        except Exception as e:
            return jsonify({"error": "Error al consultar la póliza", "detalle": str(e)}), 500

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

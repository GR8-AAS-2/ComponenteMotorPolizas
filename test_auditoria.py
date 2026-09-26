import unittest
from unittest.mock import patch, MagicMock
import json
import jwt
from datetime import datetime, timedelta, timezone
from app import create_app
from models import db, Poliza
from auditoria import (
    normalizar_8_campos_poliza,
    validar_poliza_con_fraude,
    registrar_hash_poliza,
    registrar_log_auditoria,
    analizar_elevacion_privilegios
)


class TestEcosistemaSeguridadPolizas(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "AUDIT_SERVICE_URL": "https://polizaseguridad.vercel.app",
            "AUDIT_API_KEY": "test-audit-key",
            "FRAUDE_SERVICE_URL": "https://motorfraude.vercel.app",
            "FRAUDE_API_KEY": "test-fraude-key",
            "RESPUESTA_SERVICE_URL": "https://motorrespuestaincidentes.vercel.app",
            "RESPUESTA_API_KEY": "test-respuesta-key"
        })
        self.client = self.app.test_client()
        self.secret_key = self.app.config["JWT_SECRET_KEY"]
        self.algorithm = self.app.config["JWT_ALGORITHM"]

        # Insertar póliza de prueba en BD en memoria
        with self.app.app_context():
            db.create_all()
            self.poliza_test = Poliza(
                numero_poliza="POL-2026-000123",
                titular="Carlos Andres Gomez",
                tipo_documento="CC",
                documento_identidad="1000000001",
                ramo="Autos",
                tipo_cobertura="Todo riesgo",
                monto_asegurado=85000000.00,
                prima_mensual=250000.00,
                deducible=1000000.00,
                fecha_inicio_vigencia=datetime.strptime("2026-01-01", "%Y-%m-%d").date(),
                fecha_fin_vigencia=datetime.strptime("2026-12-31", "%Y-%m-%d").date(),
                estado="ACTIVA"
            )
            db.session.add(self.poliza_test)
            db.session.commit()

        # Token JWT de prueba
        token_payload = {
            "codigo_usuario": "usr-042",
            "rol": "CONSULTOR",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        self.token = jwt.encode(token_payload, self.secret_key, algorithm=self.algorithm)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Forwarded-For": "203.0.113.5"
        }

    def test_normalizar_8_campos_poliza(self):
        """Verifica la normalización exacta de los 8 campos requeridos por el Motor de Fraude"""
        raw_data = {
            "numero_poliza": "POL-2026-000123",
            "tipo_documento": "CC",
            "documento_identidad": "1000000001",
            "ramo": "Autos",
            "tipo_cobertura": "Todo riesgo",
            "monto_asegurado": 85000000.0,
            "fecha_inicio_vigencia": "2026-01-01",
            "fecha_fin_vigencia": "2026-12-31",
            "campo_extra_ignorado": "ignorar"
        }
        normalizados = normalizar_8_campos_poliza(raw_data)

        self.assertEqual(normalizados["numero_poliza"], "POL-2026-000123")
        self.assertEqual(normalizados["tipo_documento"], "CC")
        self.assertEqual(normalizados["documento_identidad"], "1000000001")
        self.assertEqual(normalizados["ramo"], "Autos")
        self.assertEqual(normalizados["tipo_cobertura"], "Todo riesgo")
        self.assertEqual(normalizados["monto_asegurado"], "85000000.00")
        self.assertEqual(normalizados["fecha_inicio_vigencia"], "2026-01-01")
        self.assertEqual(normalizados["fecha_fin_vigencia"], "2026-12-31")
        self.assertNotIn("campo_extra_ignorado", normalizados)

    @patch("auditoria.requests.post")
    def test_validacion_directa_exitosa(self, mock_post):
        """Si el Motor de Fraude responde 'directo', la API entrega la póliza íntegra"""
        # Mock de respuesta del motor de fraude
        mock_resp_fraude = MagicMock()
        mock_resp_fraude.status_code = 200
        mock_resp_fraude.json.return_value = {
            "numero_poliza": "POL-2026-000123",
            "hash_coincide": True,
            "verificacion": "directo",
            "datos_correctos": {
                "numero_poliza": "POL-2026-000123",
                "monto_asegurado": "85000000.00"
            }
        }

        # Mock de respuesta de auditoría
        mock_resp_audit = MagicMock()
        mock_resp_audit.status_code = 201
        mock_resp_audit.json.return_value = {"id": "log-001"}

        mock_post.side_effect = [mock_resp_fraude, mock_resp_audit]

        response = self.client.get("/api/polizas/1", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["numero_poliza"], "POL-2026-000123")

    @patch("auditoria.requests.post")
    def test_validacion_log_auditoria_recupera_datos(self, mock_post):
        """Si los datos en BD fueron alterados, se recuperan los datos genuinos desde auditoría"""
        mock_resp_fraude = MagicMock()
        mock_resp_fraude.status_code = 200
        mock_resp_fraude.json.return_value = {
            "numero_poliza": "POL-2026-000123",
            "hash_coincide": False,
            "verificacion": "log_auditoria",
            "datos_correctos": {
                "numero_poliza": "POL-2026-000123",
                "monto_asegurado": "85000000.00"
            },
            "mensaje": "Los datos recibidos no coinciden con el hash, pero se recuperaron del log de auditoría."
        }

        mock_resp_audit = MagicMock()
        mock_resp_audit.status_code = 201
        mock_resp_audit.json.return_value = {"id": "log-002"}

        mock_post.side_effect = [mock_resp_fraude, mock_resp_audit]

        response = self.client.get("/api/polizas/1", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["monto_asegurado"], "85000000.00")

    @patch("auditoria.requests.post")
    def test_validacion_sin_confirmar_posible_fraude(self, mock_post):
        """Si el hash no coincide y no se puede confirmar en auditoría, se bloquea y retorna alerta"""
        mock_resp_fraude = MagicMock()
        mock_resp_fraude.status_code = 200
        mock_resp_fraude.json.return_value = {
            "numero_poliza": "POL-2026-000123",
            "hash_coincide": False,
            "verificacion": "sin_confirmar",
            "datos_correctos": None,
            "mensaje": "El hash no coincide y no se pudo confirmar contra el log de auditoría. Posible alteración de los datos de la póliza."
        }

        mock_resp_audit = MagicMock()
        mock_resp_audit.status_code = 201
        mock_resp_audit.json.return_value = {"id": "alerta-001"}

        mock_post.side_effect = [mock_resp_fraude, mock_resp_audit]

        response = self.client.get("/api/polizas/1", headers=self.headers)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["verificacion"], "sin_confirmar")
        self.assertFalse(data["hash_coincide"])

    @patch("auditoria.requests.post")
    def test_envio_headers_x_api_key(self, mock_post):
        """Verifica que las peticiones a los motores de seguridad incluyan la cabecera X-API-Key"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"verificacion": "directo", "hash_coincide": True}
        mock_post.return_value = mock_response

        with self.app.app_context():
            validar_poliza_con_fraude({"numero_poliza": "POL-2026-000123"})

        self.assertTrue(mock_post.called)
        _, kwargs = mock_post.call_args
        self.assertIn("X-API-Key", kwargs["headers"])
        self.assertEqual(kwargs["headers"]["X-API-Key"], "test-fraude-key")

    @patch("auditoria.requests.post")
    def test_creacion_poliza_con_registro_hash_exitoso(self, mock_post):
        """Verifica que al crear póliza se registre el hash en Motor de Fraude y el log en Auditoría"""
        # 1. Mock de respuesta de POST /api/polizas/hash (Motor de Fraude) -> 201 Created
        mock_resp_fraude = MagicMock()
        mock_resp_fraude.status_code = 201
        mock_resp_fraude.json.return_value = {
            "id": "hash-uuid-001",
            "numero_poliza": "POL-2026-NUEVA-999",
            "hash": "5f2c...e91a",
            "fecha_creacion": "2026-09-25T05:20:00+00:00"
        }

        # 2. Mock de respuesta de POST /api/logs (Auditoría Central) -> 201 Created
        mock_resp_audit = MagicMock()
        mock_resp_audit.status_code = 201
        mock_resp_audit.json.return_value = {"id": "audit-uuid-001"}

        mock_post.side_effect = [mock_resp_fraude, mock_resp_audit]

        payload_nueva_poliza = {
            "numero_poliza": "POL-2026-NUEVA-999",
            "titular": "Ana Maria Torres",
            "tipo_documento": "CC",
            "documento_identidad": "1020304050",
            "ramo": "Vida",
            "tipo_cobertura": "Vida Individual",
            "monto_asegurado": 120000000.00,
            "fecha_inicio_vigencia": "2026-01-01",
            "fecha_fin_vigencia": "2036-01-01"
        }

        response = self.client.post("/api/polizas", headers=self.headers, json=payload_nueva_poliza)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn("poliza", data)
        self.assertIn("hash_seguridad", data)
        self.assertEqual(data["poliza"]["numero_poliza"], "POL-2026-NUEVA-999")

        # Verificar que se hicieron 2 llamadas POST: 1 a fraude y 1 a auditoría
        self.assertEqual(mock_post.call_count, 2)
        llamada_fraude = mock_post.call_args_list[0]
        llamada_audit = mock_post.call_args_list[1]

        # Verificar payload a fraude (los 8 campos normalizados)
        self.assertIn("numero_poliza", llamada_fraude[1]["json"])
        self.assertEqual(llamada_fraude[1]["json"]["monto_asegurado"], "120000000.00")

        # Verificar payload a auditoría (tipo_evento=Poliza, evento=Create)
        self.assertEqual(llamada_audit[1]["json"]["tipo_evento"], "Poliza")
        self.assertEqual(llamada_audit[1]["json"]["evento"], "Create")
        self.assertEqual(llamada_audit[1]["json"]["identificador"], "POL-2026-NUEVA-999")

    @patch("auditoria.requests.post")
    def test_creacion_poliza_falla_si_fraude_rechaza_hash(self, mock_post):
        """Si el Motor de Fraude responde 409 Conflict, la creación se detiene y devuelve 409"""
        mock_resp_fraude = MagicMock()
        mock_resp_fraude.status_code = 409
        mock_resp_fraude.json.return_value = {
            "error": "Ya existe un hash registrado para la póliza 'POL-2026-EXISTE-001'. No se sobrescribe."
        }
        mock_post.return_value = mock_resp_fraude

        payload = {
            "numero_poliza": "POL-2026-EXISTE-001",
            "titular": "Juan Perez",
            "tipo_documento": "CC",
            "documento_identidad": "12345678",
            "ramo": "Autos",
            "tipo_cobertura": "Todo riesgo",
            "monto_asegurado": 50000000.00,
            "fecha_inicio_vigencia": "2026-01-01",
            "fecha_fin_vigencia": "2027-01-01"
        }

        response = self.client.post("/api/polizas", headers=self.headers, json=payload)
        self.assertEqual(response.status_code, 409)

    @patch("auditoria.requests.post")
    def test_endpoint_elevacion_privilegios_vulneracion_detectada(self, mock_post):
        """Verifica que primero registre en auditoría y luego consulte al motor de incidentes"""
        # 1. Mock de POST /api/logs (Auditoría Central)
        mock_resp_audit = MagicMock()
        mock_resp_audit.status_code = 201
        mock_resp_audit.json.return_value = {"id": "log-cambio-rol-123"}

        # 2. Mock de POST /api/incidentes/elevacion-privilegios (Motor de Incidentes)
        mock_resp_incidente = MagicMock()
        mock_resp_incidente.status_code = 200
        mock_resp_incidente.json.return_value = {
            "usuario_id": "usr-001",
            "estado": "vulneracion_detectada",
            "vulneracion_detectada": True,
            "accion": "revocar_permisos",
            "mensaje": "Se ha presentado una vulneración: el último cambio de rol se realizó desde una IP distinta a la habitual del usuario.",
            "ip_ultimo_cambio": "198.51.100.99",
            "ip_habitual": "203.0.113.20",
            "total_eventos_analizados": 4,
            "incidente_registrado": True,
            "incidente_log_id": "9d3e2f10-7a6b-4c5d-8e9f-0a1b2c3d4e5f"
        }

        mock_post.side_effect = [mock_resp_audit, mock_resp_incidente]

        payload = {
            "usuario_id": "usr-001",
            "identificador": "cambio-rol-7781",
            "rol_anterior": "consulta",
            "rol_nuevo": "admin",
            "ip_origen": "203.0.113.25"
        }
        response = self.client.post("/api/incidentes/elevacion-privilegios", headers=self.headers, json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["vulneracion_detectada"])
        self.assertEqual(data["accion"], "revocar_permisos")
        self.assertEqual(data["estado"], "vulneracion_detectada")

        # Verificar que se hicieron 2 llamadas POST: 1 a auditoría y 1 a incidentes
        self.assertEqual(mock_post.call_count, 2)
        llamada_audit = mock_post.call_args_list[0]
        llamada_incidente = mock_post.call_args_list[1]

        # 1. Validar llamada a auditoría
        self.assertEqual(llamada_audit[1]["json"]["tipo_evento"], "Seguridad")
        self.assertEqual(llamada_audit[1]["json"]["evento"], "New_Rol")
        self.assertEqual(llamada_audit[1]["json"]["identificador"], "cambio-rol-7781")
        self.assertEqual(llamada_audit[1]["json"]["usuario_id"], "usr-001")
        self.assertEqual(llamada_audit[1]["json"]["ip_origen"], "203.0.113.25")
        self.assertEqual(llamada_audit[1]["json"]["detalle"], {"rol_anterior": "consulta", "rol_nuevo": "admin"})

        # 2. Validar llamada a motor de incidentes
        self.assertEqual(llamada_incidente[1]["json"]["usuario_id"], "usr-001")
        self.assertIn("X-API-Key", llamada_incidente[1]["headers"])

    @patch("auditoria.requests.post")
    def test_endpoint_elevacion_privilegios_sin_cambios(self, mock_post):
        """Verifica la respuesta cuando el cambio de rol fue desde la IP habitual"""
        mock_resp_audit = MagicMock()
        mock_resp_audit.status_code = 201
        mock_resp_audit.json.return_value = {"id": "log-001"}

        mock_resp_incidente = MagicMock()
        mock_resp_incidente.status_code = 200
        mock_resp_incidente.json.return_value = {
            "usuario_id": "usr-042",
            "estado": "sin_cambios",
            "vulneracion_detectada": False,
            "accion": None,
            "mensaje": "No hubo cambios: el último cambio de rol se realizó desde la IP habitual del usuario.",
            "ip_ultimo_cambio": "203.0.113.5",
            "ip_habitual": "203.0.113.5",
            "total_eventos_analizados": 3
        }

        mock_post.side_effect = [mock_resp_audit, mock_resp_incidente]

        # Llamada omitiendo usuario_id para que use el del token (usr-042)
        response = self.client.post("/api/incidentes/elevacion-privilegios", headers=self.headers, json={})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data["vulneracion_detectada"])
        self.assertIsNone(data["accion"])


if __name__ == "__main__":
    unittest.main()

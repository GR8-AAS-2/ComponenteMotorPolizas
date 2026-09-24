import unittest
from unittest.mock import patch, MagicMock
import json
import jwt
from datetime import datetime, timedelta, timezone
from app import create_app
from models import db, Poliza

class TestAuditoriaIntegracion(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
        })
        self.client = self.app.test_client()
        self.secret_key = self.app.config["JWT_SECRET_KEY"]
        self.algorithm = self.app.config["JWT_ALGORITHM"]

        # Token de prueba
        token_payload = {
            "codigo_usuario": "USR_AUDITOR",
            "rol": "CONSULTOR",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        self.token = jwt.encode(token_payload, self.secret_key, algorithm=self.algorithm)
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @patch("auditoria.requests.post")
    def test_auditoria_flag_true_retorna_datos(self, mock_post):
        """Si auditoría responde flag=True, la API devuelve los datos con normalidad"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "flag": True,
            "mensaje": "Hash de integridad verificado con éxito"
        }
        mock_post.return_value = mock_response

        response = self.client.get("/api/polizas", headers=self.headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("data", data)
        self.assertIn("usuario_autenticado", data)
        self.assertEqual(data["usuario_autenticado"], "USR_AUDITOR")

    @patch("auditoria.requests.post")
    def test_auditoria_flag_false_retorna_respuesta_auditoria(self, mock_post):
        """Si auditoría responde flag=False, la API devuelve directamente la respuesta de auditoría"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        respuesta_esperada_auditoria = {
            "flag": False,
            "error": "Violación de integridad",
            "motivo": "El hash de la póliza no coincide con el registro original de auditoría",
            "timestamp": "2026-09-21T21:00:00Z"
        }
        mock_response.json.return_value = respuesta_esperada_auditoria
        mock_post.return_value = mock_response

        response = self.client.get("/api/polizas", headers=self.headers)
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["flag"], False)
        self.assertEqual(data["error"], "Violación de integridad")
        self.assertEqual(data["motivo"], "El hash de la póliza no coincide con el registro original de auditoría")

    @patch("auditoria.requests.post")
    def test_auditoria_envia_ip_cliente(self, mock_post):
        """Verifica que los datos de póliza, usuario, rol e IP se envíen al servicio de auditoría"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"flag": True}
        mock_post.return_value = mock_response

        headers_con_ip = {
            **self.headers,
            "X-Forwarded-For": "198.51.100.42, 10.0.0.1"
        }
        self.client.get("/api/polizas", headers=headers_con_ip)

        self.assertTrue(mock_post.called)
        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        self.assertIn("datos", payload)
        self.assertEqual(payload["codigo_usuario"], "USR_AUDITOR")
        self.assertEqual(payload["rol"], "CONSULTOR")
        self.assertEqual(payload["ip_origen"], "198.51.100.42")


if __name__ == "__main__":
    unittest.main()

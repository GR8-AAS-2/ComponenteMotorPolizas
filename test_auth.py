import unittest
import json
import jwt
from datetime import datetime, timedelta, timezone
from app import create_app
from config import Config

class TestJWTAuth(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
        })
        self.client = self.app.test_client()
        self.secret_key = self.app.config["JWT_SECRET_KEY"]
        self.algorithm = self.app.config["JWT_ALGORITHM"]

    def _create_token(self, payload, expired=False, invalid_secret=False):
        now = datetime.now(timezone.utc)
        exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
        data = {"exp": exp, **payload}
        key = "wrong-secret-key-that-is-at-least-32-chars-long" if invalid_secret else self.secret_key
        return jwt.encode(data, key, algorithm=self.algorithm)

    def test_missing_authorization_header(self):
        """Petición sin cabecera Authorization debe retornar 401"""
        response = self.client.get("/api/polizas")
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn("Cabecera 'Authorization' faltante", data.get("mensaje", ""))

    def test_invalid_bearer_format(self):
        """Petición con formato inválido debe retornar 401"""
        response = self.client.get("/api/polizas", headers={"Authorization": "Basic 12345"})
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn("Formato de token inválido", data.get("mensaje", ""))

    def test_invalid_signature(self):
        """Token firmado con clave errónea debe retornar 401"""
        token = self._create_token({"codigo_usuario": "USR001", "rol": "ADMIN"}, invalid_secret=True)
        response = self.client.get("/api/polizas", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn("Firma del token inválida", data.get("mensaje", ""))

    def test_expired_token(self):
        """Token expirado debe retornar 401"""
        token = self._create_token({"codigo_usuario": "USR001", "rol": "ADMIN"}, expired=True)
        response = self.client.get("/api/polizas", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn("El token ha expirado", data.get("mensaje", ""))

    def test_missing_codigo_usuario_claim(self):
        """Token sin codigo_usuario debe retornar 401"""
        token = self._create_token({"rol": "ADMIN"})
        response = self.client.get("/api/polizas", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn("código de usuario", data.get("mensaje", ""))

    def test_missing_rol_claim(self):
        """Token sin claim de rol debe retornar 401"""
        token = self._create_token({"codigo_usuario": "USR001"})
        response = self.client.get("/api/polizas", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn("claim de rol", data.get("mensaje", ""))

    def test_insufficient_role(self):
        """Token con rol no permitido en endpoint protegido por rol debe retornar 403"""
        from auth import token_required

        @self.app.route("/test-solo-admin")
        @token_required(allowed_roles=["ADMIN", "SUPERVISOR"])
        def ruta_admin():
            return {"status": "ok"}

        token = self._create_token({"codigo_usuario": "USR_GUEST", "rol": "INVITADO"})
        response = self.client.get("/test-solo-admin", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertIn("no autorizado para esta operación", data.get("mensaje", ""))

    def test_public_health_endpoint(self):
        """El endpoint /health no debe requerir token"""
        response = self.client.get("/health")
        # Responderá status 200 o 500 (dependiendo de si hay DB conectada), pero no 401
        self.assertIn(response.status_code, [200, 500])

if __name__ == "__main__":
    unittest.main()

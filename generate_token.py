"""
Script utilitario para generar tokens JWT de prueba para la API Motor de Pólizas.
Uso:
    python generate_token.py --usuario USR_ADMIN --rol ADMIN --exp 24
"""
import argparse
import os
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv

load_dotenv()

def generar_token(codigo_usuario="USR_DEV_01", rol="ADMIN", horas_exp=24):
    secret_key = os.getenv("JWT_SECRET_KEY", "motor_polizas_super_secret_jwt_key_2026_segura_32bytes")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")

    payload = {
        "codigo_usuario": codigo_usuario,
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(hours=horas_exp),
        "iat": datetime.now(timezone.utc)
    }

    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token, payload

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de tokens JWT para pruebas")
    parser.add_argument("--usuario", default="USR_DEV_01", help="Código de usuario (default: USR_DEV_01)")
    parser.add_argument("--rol", default="ADMIN", help="Rol del usuario: ADMIN, SUPERVISOR, CONSULTOR (default: ADMIN)")
    parser.add_argument("--exp", type=int, default=24, help="Horas de vigencia del token (default: 24)")

    args = parser.parse_args()
    token, payload = generar_token(args.usuario, args.rol, args.exp)

    print("\n" + "="*65)
    print("[+] TOKEN JWT GENERADO EXITOSAMENTE")
    print("="*65)
    print(f"Usuario: {payload['codigo_usuario']}")
    print(f"Rol:     {payload['rol']}")
    print(f"Expira:  {payload['exp']}")
    print("\nToken:\n")
    print(token)
    print("\n" + "="*65)
    print("Comandos de prueba:")
    print("1. Consultar todas las polizas:")
    print(f'   curl -X GET http://localhost:5000/api/polizas -H "Authorization: Bearer {token}"')
    print("\n2. Consultar poliza por ID:")
    print(f'   curl -X GET http://localhost:5000/api/polizas/1 -H "Authorization: Bearer {token}"')
    print("="*65 + "\n")

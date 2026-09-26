"""
Script de prueba para el endpoint POST /api/polizas.
Crea una póliza en la base de datos real (PostgreSQL/Supabase) y la deja guardada (no la elimina).
"""
import time
import requests
from unittest.mock import patch, MagicMock
from app import create_app
from models import db, Poliza
from generate_token import generar_token

def probar_creacion_poliza():
    app = create_app()
    client = app.test_client()

    # 1. Generar token de prueba
    token, _ = generar_token(codigo_usuario="USR_PRUEBA_CREACION", rol="ADMIN", horas_exp=24)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Forwarded-For": "190.24.55.12"
    }

    # 2. Generar número único de póliza para la prueba
    num_unico = f"POL-2026-AUT-TEST-{int(time.time())}"
    payload_poliza = {
        "numero_poliza": num_unico,
        "titular": "Valeria Sofia Mendoza",
        "tipo_documento": "CC",
        "documento_identidad": "1098765432",
        "email_titular": "valeria.mendoza@email.com",
        "telefono_titular": "+57 3124567890",
        "direccion": "Carrera 43A # 1Sur-100",
        "ciudad": "Medellín",
        "ramo": "Autos",
        "tipo_cobertura": "Todo riesgo Premium Gold",
        "monto_asegurado": 95000000.00,
        "prima_mensual": 280000.00,
        "deducible": 1500000.00,
        "fecha_inicio_vigencia": "2026-03-01",
        "fecha_fin_vigencia": "2027-03-01",
        "frecuencia_pago": "MENSUAL",
        "metodo_pago": "DEBITO_AUTOMATICO",
        "agente_codigo": "AGT-01",
        "agente_nombre": "Laura Martinez",
        "beneficiarios": "Titular (100%)"
    }

    print("\n" + "="*70)
    print("[*] INICIANDO PRUEBA DE CREACION DE POLIZA (POST /api/polizas)")
    print("="*70)
    print(f"Numero de Poliza a crear: {num_unico}")
    print(f"Titular:                 {payload_poliza['titular']}")
    print(f"Monto Asegurado:         ${payload_poliza['monto_asegurado']:,.2f}")
    print("="*70)

    # Verificamos si se tienen API Keys reales configuradas o si simulamos la respuesta del motor de fraude
    fraude_key = app.config.get("FRAUDE_API_KEY", "")
    usar_mock = not fraude_key or fraude_key == "fraude_secret_key_aqui"

    if usar_mock:
        print("[i] Simulando respuesta exitosa del Motor de Fraude y Auditoria (X-API-Key de prueba)...")
        with patch("auditoria.requests.post") as mock_post:
            mock_resp_fraude = MagicMock()
            mock_resp_fraude.status_code = 201
            mock_resp_fraude.json.return_value = {
                "id": "hash-uuid-live-test",
                "numero_poliza": num_unico,
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "fecha_creacion": "2026-09-25T20:30:00+00:00"
            }

            mock_resp_audit = MagicMock()
            mock_resp_audit.status_code = 201
            mock_resp_audit.json.return_value = {"id": "log-audit-live-test"}

            mock_post.side_effect = [mock_resp_fraude, mock_resp_audit]

            response = client.post("/api/polizas", headers=headers, json=payload_poliza)
    else:
        print("[*] Conectando directamente con el Motor de Fraude y Auditoria en produccion...")
        response = client.post("/api/polizas", headers=headers, json=payload_poliza)

    print(f"\n[+] Codigo de respuesta HTTP: {response.status_code}")
    data = response.get_json()
    print("\n[+] Respuesta del Endpoint:")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # 3. Validar en la base de datos que la póliza quedó persistida
    with app.app_context():
        poliza_guardada = Poliza.query.filter_by(numero_poliza=num_unico).first()
        if poliza_guardada:
            print("\n" + "="*70)
            print("[OK] VERIFICACION EN BASE DE DATOS: POLIZA GUARDADA EXITOSAMENTE")
            print("="*70)
            print(f"ID en Base de Datos: {poliza_guardada.id}")
            print(f"Numero de Poliza:    {poliza_guardada.numero_poliza}")
            print(f"Titular:             {poliza_guardada.titular}")
            print(f"Monto Asegurado:     ${float(poliza_guardada.monto_asegurado):,.2f}")
            print(f"Estado:              {poliza_guardada.estado}")
            print(f"Fecha Creacion:      {poliza_guardada.fecha_creacion}")
            print("\n[!] NOTA: La poliza NO ha sido eliminada y permanece registrada en PostgreSQL.")
            print("="*70 + "\n")
        else:
            print("\n[X] Error: La poliza no se encontro en la base de datos.")

if __name__ == "__main__":
    probar_creacion_poliza()

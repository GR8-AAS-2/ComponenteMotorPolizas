"""
Script para probar la consulta de la póliza creada con validación de hash en el Motor de Fraude y registro en Auditoría.
"""
import json
from app import create_app
from models import db, Poliza
from generate_token import generar_token
from auditoria import validar_poliza_con_fraude, normalizar_8_campos_poliza

def probar_consulta_poliza():
    app = create_app()
    client = app.test_client()

    # 1. Obtener la última póliza insertada
    with app.app_context():
        poliza = Poliza.query.filter(Poliza.numero_poliza.like("POL-2026-AUT-TEST-%")).order_by(Poliza.id.desc()).first()
        if not poliza:
            # Fallback a la última póliza general
            poliza = Poliza.query.order_by(Poliza.id.desc()).first()

        if not poliza:
            print("[X] No se encontraron pólizas en la base de datos.")
            return

        poliza_id = poliza.id
        num_poliza = poliza.numero_poliza
        poliza_dict = poliza.to_dict()

    print("\n" + "="*75)
    print(f"[*] CONSULTANDO PÓLIZA ID: {poliza_id} ({num_poliza})")
    print("="*75)

    # 2. Generar token de autenticación
    token, _ = generar_token(codigo_usuario="USR_CONSULTA_HASH", rol="ADMIN", horas_exp=24)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Forwarded-For": "190.24.55.12"
    }

    # 3. Prueba directa contra el Motor de Fraude (POST /api/polizas/validar)
    print("\n[1] LLAMADA DIRECTA AL MOTOR DE FRAUDE (POST /api/polizas/validar):")
    campos_8 = normalizar_8_campos_poliza(poliza_dict)
    print("Payload enviado (8 campos normalizados):")
    print(json.dumps(campos_8, indent=2))

    with app.app_context():
        es_valido, res_fraude, status_fraude = validar_poliza_con_fraude(poliza_dict)
        print(f"\nRespuesta del Motor de Fraude (Status {status_fraude}):")
        print(json.dumps(res_fraude, indent=2, ensure_ascii=False))
        print(f"Integridad Validada: {'SI (Hash coincide)' if es_valido else 'NO (Fraude o alteracion)'}")

    # 4. Prueba a través del Endpoint GET /api/polizas/<id>
    print("\n" + "-"*75)
    print(f"[2] LLAMADA AL ENDPOINT DE LA API (GET /api/polizas/{poliza_id}):")
    resp_endpoint = client.get(f"/api/polizas/{poliza_id}", headers=headers)
    print(f"HTTP Status: {resp_endpoint.status_code}")
    print("Respuesta Endpoint:")
    print(json.dumps(resp_endpoint.get_json(), indent=2, ensure_ascii=False))

    print("\n" + "="*75)
    print("[OK] PRUEBA DE CONSULTA Y VALIDACIÓN DE HASH FINALIZADA")
    print("="*75 + "\n")

if __name__ == "__main__":
    probar_consulta_poliza()

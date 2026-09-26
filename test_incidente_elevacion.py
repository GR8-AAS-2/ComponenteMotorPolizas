"""
Script de prueba para el endpoint POST /api/incidentes/elevacion-privilegios
Conecta directamente con el Servicio Central de Auditoria y el Motor de Respuesta a Incidentes en produccion.
"""
import json
import time
from app import create_app
from generate_token import generar_token

def probar_elevacion_privilegios():
    app = create_app()
    client = app.test_client()

    usuario_test = f"USR_TEST_ELEVACION_{int(time.time())}"
    ip_habitual = "190.24.55.12"
    ip_sospechosa = "200.89.120.45"

    token, _ = generar_token(codigo_usuario=usuario_test, rol="CONSULTA", horas_exp=24)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Forwarded-For": ip_habitual
    }

    print("\n" + "="*75)
    print("[*] TEST: EVALUACIÓN DE ELEVACIÓN DE PRIVILEGIOS")
    print(f"    Usuario: {usuario_test}")
    print(f"    Servicio Auditoría: {app.config.get('AUDIT_SERVICE_URL')}")
    print(f"    Motor Incidentes:   {app.config.get('RESPUESTA_SERVICE_URL')}")
    print("="*75)

    # Paso 1: Establecer IP habitual con eventos previos
    print("\n[Paso 1] Estableciendo historial con IP habitual (190.24.55.12)...")
    for i in range(1, 4):
        payload_prev = {
            "usuario_id": usuario_test,
            "rol_anterior": "INVITADO",
            "rol_nuevo": "CONSULTA",
            "ip_origen": ip_habitual
        }
        client.post("/api/incidentes/elevacion-privilegios", headers=headers, json=payload_prev)
    print("  -> 3 eventos registrados con éxito desde la IP habitual.")

    # Paso 2: Registrar elevación sospechosa desde IP anómala
    print("\n" + "-"*75)
    print(f"[Paso 2] Registrando elevación a ADMIN desde IP anómala ({ip_sospechosa})...")
    payload_2 = {
        "usuario_id": usuario_test,
        "rol_anterior": "CONSULTA",
        "rol_nuevo": "ADMIN",
        "ip_origen": ip_sospechosa
    }
    headers["X-Forwarded-For"] = ip_sospechosa
    resp2 = client.post("/api/incidentes/elevacion-privilegios", headers=headers, json=payload_2)
    print(f"HTTP Status: {resp2.status_code}")
    print("Respuesta del Motor de Incidentes:")
    print(json.dumps(resp2.get_json(), indent=2, ensure_ascii=False))

    print("\n" + "="*75)
    print("[OK] PRUEBA DE EVALUACIÓN DE ELEVACIÓN DE PRIVILEGIOS FINALIZADA")
    print("="*75 + "\n")

if __name__ == "__main__":
    probar_elevacion_privilegios()

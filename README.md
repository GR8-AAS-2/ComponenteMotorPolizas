# Componente Motor de Pólizas - API en Flask con PostgreSQL y Auditoría

API REST desarrollada con **Flask** y **Flask-SQLAlchemy**, conectada a una base de datos **PostgreSQL**, protegida con autenticación **JWT**, control de acceso por roles e integración automática con un **Servicio de Auditoría e Integridad** (con validación de hash y registro de IP de origen).

---

## 📋 Requisitos Previos

- Python 3.10 o superior
- Instancia activa de PostgreSQL (local o remota en la nube como Neon, Supabase, AWS RDS, etc.)

---

## ⚙️ Instalación y Configuración

### 1. Crear y activar un entorno virtual

En Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Copia o edita el archivo `.env` con los parámetros correspondientes:

```ini
# Base de Datos PostgreSQL
DATABASE_URL=postgresql://<usuario>:<contraseña>@<host>:<puerto>/<nombre_base_datos>

# Servidor Flask
PORT=5000
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key-12345

# Autenticación JWT
JWT_SECRET_KEY=motor_polizas_super_secret_jwt_key_2026_segura_32bytes
JWT_ALGORITHM=HS256

# Microservicio de Auditoría
AUDITORIA_SERVICE_URL=http://localhost:5001/api/auditoria/verificar-integridad
AUDITORIA_TIMEOUT=5.0
```

> **Nota:** Si tu proveedor de base de datos te da una URL que empieza con `postgres://`, el sistema la normalizará automáticamente a `postgresql://`.

### 4. Cargar datos de prueba (Seed)

Para poblar la base de datos con pólizas de prueba iniciales:

```powershell
python seed_data.py
```

*(O puedes ejecutar el script SQL `seed.sql` directamente en tu gestor de base de datos).*

---

## 🚀 Ejecución

Para iniciar el servidor de desarrollo:

```powershell
python app.py
```

El servidor estará disponible en `http://localhost:5000`. Al arrancar, creará automáticamente las tablas en PostgreSQL si aún no existen.

---

## 🔐 Autenticación y Autorización con JWT

La API valida tokens JWT en la cabecera HTTP `Authorization: Bearer <token>`.

### Requisitos del Token JWT:
1. **Firma válida**: Firmado con el secreto configurado en `JWT_SECRET_KEY` usando el algoritmo `JWT_ALGORITHM` (`HS256`).
2. **Vigencia**: El token no debe estar expirado (claim `exp`).
3. **Código de Usuario**: Debe contener el claim `codigo_usuario` (o `sub` / `user_id`).
4. **Rol de Usuario**: Debe contener el claim `rol` (o `role`).

### Generación rápida de Tokens de prueba:
Puedes usar el script utilitario [generate_token.py](file:///d:/Proyectos/ArquitecturaAgiles/ComponenteMotorPolizas/generate_token.py):

```powershell
# Generar token para rol ADMIN (por defecto)
python generate_token.py

# Generar token con usuario, rol y vigencia personalizados
python generate_token.py --usuario USR-CONSULTOR-01 --rol CONSULTOR --exp 48
```

---

## 🛡️ Integración con Servicio de Auditoría

En cada consulta de pólizas (`GET /api/polizas` y `GET /api/polizas/<id>`), antes de retornar los datos al cliente, el sistema valida la integridad de los datos contra el microservicio de auditoría.

### 📤 Payload enviado a Auditoría

El Motor de Pólizas realiza una petición `POST` al endpoint configurado en `AUDITORIA_SERVICE_URL` con el siguiente cuerpo JSON:

```json
{
  "datos": [
    {
      "id": 1,
      "numero_poliza": "POL-2026-AUT-001",
      "titular": "Carlos Andres Gomez Diaz",
      "tipo_documento": "CC",
      "documento_identidad": "1017123456",
      "email_titular": "carlos.gomez@email.com",
      "telefono_titular": "+57 3104567890",
      "direccion": "Calle 45 # 23-10",
      "ciudad": "Bogotá",
      "ramo": "Autos",
      "tipo_cobertura": "Todo Riesgo Premium Plus",
      "monto_asegurado": 65000000.00,
      "prima_mensual": 245000.00,
      "deducible": 1000000.00,
      "fecha_inicio_vigencia": "2026-01-01",
      "fecha_fin_vigencia": "2027-01-01",
      "frecuencia_pago": "MENSUAL",
      "metodo_pago": "DEBITO_AUTOMATICO",
      "estado": "ACTIVA",
      "agente_codigo": "AGT-01",
      "agente_nombre": "Laura Martinez",
      "beneficiarios": "Titular",
      "fecha_creacion": "2026-03-24T10:00:00",
      "fecha_actualizacion": "2026-03-24T10:00:00"
    }
  ],
  "codigo_usuario": "USR_ADMIN",
  "rol": "ADMIN",
  "ip_origen": "190.24.55.12"
}
```

#### Detalle de los campos enviados a Auditoría:
| Campo | Tipo | Descripción |
|---|---|---|
| `datos` | `Array` / `Object` | Información de la(s) póliza(s) consultada(s) para validar su hash o integridad. |
| `codigo_usuario` | `String` | Identificador del usuario que realiza la petición, extraído del token JWT. |
| `rol` | `String` | Rol del usuario autenticado (`ADMIN`, `SUPERVISOR`, `CONSULTOR`, etc.). |
| `ip_origen` | `String` | Dirección IP real del cliente (obtenida de la cabecera `X-Forwarded-For` o de `request.remote_addr`). |

### 📥 Procesamiento de la Respuesta de Auditoría
- Si auditoría confirma la integridad (`flag: true` o status `200`), la API entrega los datos de las pólizas al usuario.
- Si auditoría detecta una alteración (`flag: false`), la API bloquea la entrega y retorna directamente el motivo y detalle emitido por auditoría.

---

## 📡 Endpoints de la API

| Método | Endpoint | Autenticación | Permisos / Roles | Descripción |
|---|---|---|---|---|
| `GET` | `/` | Pública | Cualquiera | Información general y catálogo de endpoints |
| `GET` | `/health` | Pública | Cualquiera | Estado de la API y verificación de conexión a PostgreSQL |
| `GET` | `/api/polizas` | Requerida (`JWT`) | Cualquier rol válido | Obtener listado de todas las pólizas (valida integridad con auditoría) |
| `GET` | `/api/polizas/<id>` | Requerida (`JWT`) | Cualquier rol válido | Obtener una póliza por ID (valida integridad con auditoría) |

---

## 🧪 Ejemplos de Consumo con cURL

### 1. Comprobar salud (Público)
```bash
curl -X GET http://localhost:5000/health
```

### 2. Consultar todas las pólizas (con validación de auditoría e IP)
```bash
curl -X GET http://localhost:5000/api/polizas \
  -H "Authorization: Bearer <TU_TOKEN_JWT>"
```

### 3. Consultar una póliza por ID
```bash
curl -X GET http://localhost:5000/api/polizas/1 \
  -H "Authorization: Bearer <TU_TOKEN_JWT>"
```

---

## 🧪 Pruebas Unitarias

Para ejecutar la suite de pruebas unitarias (autenticación, claims JWT e integración con auditoría):

```powershell
python -m unittest discover
```

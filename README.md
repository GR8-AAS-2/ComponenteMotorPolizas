
## 1. Construcción y Generación del Token JWT

Todos los endpoints protegidos del servicio requieren un token **JSON Web Token (JWT)** enviado en la cabecera HTTP `Authorization`:

```http
Authorization: Bearer <TU_TOKEN_JWT>
```

### 1.1. Estructura y Parámetros del Token

* **Algoritmo**: `HS256` (HMAC con SHA-256)
* **Clave Secreta (`Secret`)**: Valor de la variable de entorno `JWT_SECRET_KEY` configurada en el servidor (definida en el archivo `.env`).
* **Estructura del Payload**:

```json
{
  "codigo_usuario": "USR_ADMIN_01",
  "rol": "ADMIN",
  "exp": 1790458800,
  "iat": 1790372400
}
```

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `codigo_usuario` | `string` | Sí | Identificador único del usuario (ej: `"USR_ADMIN"`, `"USR_CONSULTOR"`, `"usr-042"`). |
| `rol` | `string` | Sí | Rol o nivel de permisos del usuario (ej: `"ADMIN"`, `"SUPERVISOR"`, `"CONSULTA"`). |
| `exp` | `integer` | Sí | Timestamp UNIX de expiración del token. |
| `iat` | `integer` | Opcional | Timestamp UNIX de emisión del token. |

---

### 1.2. Cómo Generar el Token

#### Opción A: Usando el script incluido (`generate_token.py`)

El proyecto incluye un script CLI para emitir tokens de prueba rápidamente:

```bash
# Token con valores por defecto (Usuario: USR_DEV_01, Rol: ADMIN, Vigencia: 24 horas)
python generate_token.py

# Token con parámetros personalizados
python generate_token.py --usuario USR_JUAN_PEREZ --rol ADMIN --exp 48
```

#### Opción B: Generación programática en Python (usando `PyJWT`)

```python
import os
import jwt
from datetime import datetime, timedelta, timezone

# Clave secreta sincronizada con el servidor (.env)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "motor_polizas_super_secret_jwt_key_2026_segura_32bytes")
ALGORITHM = "HS256"

payload = {
    "codigo_usuario": "USR_ADMIN_01",
    "rol": "ADMIN",
    "iat": datetime.now(timezone.utc),
    "exp": datetime.now(timezone.utc) + timedelta(hours=24)
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(f"Bearer {token}")
```

#### Opción C: Generación manual en [jwt.io](https://jwt.io)
1. Selecciona el algoritmo **`HS256`**.
2. En el panel **PAYLOAD: DATA**, ingresar el JSON con `codigo_usuario`, `rol` y `exp`.
3. En el panel **VERIFY SIGNATURE**, ingresar la clave secreta `motor_polizas_super_secret_jwt_key_2026_segura_32bytes`.

---

## 2. Creación de Pólizas (`POST /api/polizas`)

Permite registrar una nueva póliza en el sistema. Este endpoint ejecuta automáticamente el flujo de seguridad criptográfica:

1. **Calcula y registra el Hash SHA-256** en el **Motor de Fraude** (`POST https://motorfraude.vercel.app/api/polizas/hash`).
2. **Registra el log inmutable** en la **Auditoría Central** (`POST https://polizaseguridad.vercel.app/api/logs`) con el tipo de evento `Poliza:Create`.
3. **Persiste los datos** en la base de datos PostgreSQL.

### 2.1. Detalles del Endpoint

* **Método**: `POST`
* **URL**: `/api/polizas`
* **Autenticación**: Requerida (`Bearer <JWT>`)
* **Headers**:
  * `Authorization: Bearer <TOKEN>`
  * `Content-Type: application/json`

### 2.2. Campos del Payload (JSON)

#### Los 8 Campos Clave de Seguridad (utilizados para el Hash SHA-256):
1. `numero_poliza` *(string, obligatorio)*: Identificador único de la póliza (ej: `"POL-2026-AUT-1001"`).
2. `tipo_documento` *(string, obligatorio)*: Tipo de documento del titular (ej: `"CC"`, `"CE"`, `"PASAPORTE"`).
3. `documento_identidad` *(string, obligatorio)*: Número de documento (ej: `"1098765432"`).
4. `ramo` *(string, obligatorio)*: Ramo del seguro (ej: `"Autos"`, `"Vida"`, `"Hogar"`, `"Salud"`).
5. `tipo_cobertura` *(string, obligatorio)*: Cobertura contratada (ej: `"Todo riesgo Premium Gold"`).
6. `monto_asegurado` *(number / float, obligatorio)*: Valor monetario asegurado (ej: `95000000.00`).
7. `fecha_inicio_vigencia` *(string YYYY-MM-DD, obligatorio)*: Fecha de inicio (ej: `"2026-03-01"`).
8. `fecha_fin_vigencia` *(string YYYY-MM-DD, obligatorio)*: Fecha de finalización (ej: `"2027-03-01"`).

#### Campos Opcionales / Complementarios:
* `titular` *(string, obligatorio)*: Nombre completo del titular asegurado.
* `email_titular` *(string)*: Correo electrónico del titular.
* `telefono_titular` *(string)*: Teléfono o celular de contacto.
* `direccion` *(string)*: Dirección de residencia o predio.
* `ciudad` *(string)*: Ciudad de residencia.
* `prima_mensual` *(number / float)*: Costo mensual de la póliza.
* `deducible` *(number / float)*: Valor del deducible pactado.
* `frecuencia_pago` *(string)*: `"MENSUAL"`, `"TRIMESTRAL"`, `"SEMESTRAL"`, `"ANUAL"`.
* `metodo_pago` *(string)*: `"DEBITO_AUTOMATICO"`, `"TARJETA_CREDITO"`, `"TRANSFERENCIA"`.
* `agente_codigo` *(string)*: Código del agente asignado.
* `agente_nombre` *(string)*: Nombre del agente.
* `beneficiarios` *(string)*: Detalle o porcentaje de beneficiarios.

### 2.3. Ejemplo de Solicitud (cURL)

```bash
curl -X POST http://localhost:5000/api/polizas \
  -H "Authorization: Bearer <TU_TOKEN_JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "numero_poliza": "POL-2026-AUT-1001",
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
  }'
```

### 2.4. Ejemplo de Respuesta Exitosa (`201 Created`)

```json
{
  "mensaje": "Póliza creada exitosamente con hash registrado en Motor de Fraude",
  "creado_por": "USR_ADMIN_01",
  "hash_seguridad": {
    "id": "7a9d4c07-ba7c-4737-8b95-547eb568e774",
    "numero_poliza": "POL-2026-AUT-1001",
    "hash": "ff6037d32a05771ba23b0968aa4efa136f4479e7aa1707f97770eb5a31ff3fb9",
    "fecha_creacion": "2026-09-26T15:23:03.532269+00:00"
  },
  "poliza": {
    "id": 52,
    "numero_poliza": "POL-2026-AUT-1001",
    "titular": "Valeria Sofia Mendoza",
    "tipo_documento": "CC",
    "documento_identidad": "1098765432",
    "email_titular": "valeria.mendoza@email.com",
    "telefono_titular": "+57 3124567890",
    "direccion": "Carrera 43A # 1Sur-100",
    "ciudad": "Medellín",
    "ramo": "Autos",
    "tipo_cobertura": "Todo riesgo Premium Gold",
    "monto_asegurado": 95000000.0,
    "prima_mensual": 280000.0,
    "deducible": 1500000.0,
    "fecha_inicio_vigencia": "2026-03-01",
    "fecha_fin_vigencia": "2027-03-01",
    "frecuencia_pago": "MENSUAL",
    "metodo_pago": "DEBITO_AUTOMATICO",
    "estado": "ACTIVA",
    "agente_codigo": "AGT-01",
    "agente_nombre": "Laura Martinez",
    "beneficiarios": "Titular (100%)",
    "fecha_creacion": "2026-09-26T15:23:06.145734",
    "fecha_actualizacion": "2026-09-26T15:23:06.145734"
  }
}
```

---

## 3. Consulta de Pólizas con Validación de Hash (`GET /api/polizas/<id>` y `GET /api/polizas`)

Permite consultar la información de una póliza individual o del listado completo asegurando que la información **no haya sido adulterada en la base de datos**.

### 3.1. Consulta de una Póliza Individual por ID

* **Método**: `GET`
* **URL**: `/api/polizas/<id>` (ejemplo: `/api/polizas/52`)
* **Headers**: `Authorization: Bearer <TU_TOKEN_JWT>`

#### Solicitud (cURL):
```bash
curl -X GET http://localhost:5000/api/polizas/52 \
  -H "Authorization: Bearer <TU_TOKEN_JWT>"
```

#### Respuesta Exitosa (`200 OK` - Integridad Confirmada):
```json
{
  "id": 52,
  "numero_poliza": "POL-2026-AUT-1001",
  "titular": "Valeria Sofia Mendoza",
  "tipo_documento": "CC",
  "documento_identidad": "1098765432",
  "email_titular": "valeria.mendoza@email.com",
  "telefono_titular": "+57 3124567890",
  "direccion": "Carrera 43A # 1Sur-100",
  "ciudad": "Medellín",
  "ramo": "Autos",
  "tipo_cobertura": "Todo riesgo Premium Gold",
  "monto_asegurado": 95000000.0,
  "prima_mensual": 280000.0,
  "deducible": 1500000.0,
  "fecha_inicio_vigencia": "2026-03-01",
  "fecha_fin_vigencia": "2027-03-01",
  "frecuencia_pago": "MENSUAL",
  "metodo_pago": "DEBITO_AUTOMATICO",
  "estado": "ACTIVA",
  "agente_codigo": "AGT-01",
  "agente_nombre": "Laura Martinez",
  "beneficiarios": "Titular (100%)",
  "fecha_creacion": "2026-09-26T15:23:06.145734",
  "fecha_actualizacion": "2026-09-26T15:23:06.145734"
}
```

### 3.2. Consulta de Todas las Pólizas

* **Método**: `GET`
* **URL**: `/api/polizas`
* **Headers**: `Authorization: Bearer <TU_TOKEN_JWT>`

#### Solicitud (cURL):
```bash
curl -X GET http://localhost:5000/api/polizas \
  -H "Authorization: Bearer <TU_TOKEN_JWT>"
```

#### Respuesta Exitosa (`200 OK`):
```json
{
  "usuario_autenticado": "USR_ADMIN_01",
  "rol": "ADMIN",
  "total": 52,
  "data": [
    {
      "id": 1,
      "numero_poliza": "POL-2026-000001",
      "titular": "Juan Carlos Pérez",
      "ramo": "Autos",
      "monto_asegurado": 85000000.0,
      "estado": "ACTIVA"
    }
  ]
}
```

---

## 4. Detección de Incidentes por Elevación de Privilegios (`POST /api/incidentes/elevacion-privilegios`)

Evalúa si un cambio de rol de usuario representa una **intrusión o anomalía de seguridad** analizando si la acción se originó desde la **IP habitual** del usuario o desde una IP no reconocida.

### 4.1. Flujo del Servicio

1. **Registra el evento de cambio de rol** (`tipo_evento: Seguridad`, `evento: New_Rol`) en la **Auditoría Central** (`POST https://polizaseguridad.vercel.app/api/logs`).
2. **Consulta el Motor de Respuesta a Incidentes** (`POST https://motorrespuestaincidentes.vercel.app/api/incidentes/elevacion-privilegios`), el cual:
   * Obtiene el historial de actividad y calcula la IP habitual del usuario.
   * Compara la IP de la solicitud actual con el historial.
   * Si la IP difiere, clasifica el evento como `vulneracion_detectada` y dispara la acción `revocar_permisos`.

### 4.2. Detalles del Endpoint

* **Método**: `POST`
* **URL**: `/api/incidentes/elevacion-privilegios`
* **Autenticación**: Requerida (`Bearer <JWT>`)
* **Headers**:
  * `Authorization: Bearer <TOKEN>`
  * `Content-Type: application/json`

### 4.3. Parámetros del Payload (JSON)

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `usuario_id` | `string` | Opcional | Identificador del usuario analizado (si se omite, se toma el `codigo_usuario` del token JWT). |
| `rol_anterior` | `string` | Opcional | Rol previo del usuario (por defecto: `"consulta"`). |
| `rol_nuevo` | `string` | Opcional | Nuevo rol asignado (por defecto: `"admin"`). |
| `ip_origen` | `string` | Opcional | IP de origen de la transacción (si se omite, se toma la IP de la conexión). |
| `identificador` | `string` | Opcional | Identificador único del evento o ticket de cambio. |
| `limite_historial` | `integer` | Opcional | Límite de logs a inspeccionar para calcular la IP habitual (por defecto: `100`). |

### 4.4. Ejemplo de Solicitud (cURL)

```bash
curl -X POST http://localhost:5000/api/incidentes/elevacion-privilegios \
  -H "Authorization: Bearer <TU_TOKEN_JWT>" \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 200.89.120.45" \
  -d '{
    "usuario_id": "USR_TEST_ELEVACION_01",
    "rol_anterior": "CONSULTA",
    "rol_nuevo": "ADMIN",
    "ip_origen": "200.89.120.45"
  }'
```

### 4.5. Respuestas del Motor de Incidentes

#### Caso 1: Vulneración Detectada (Cambio de rol desde IP anómala)
```json
{
  "usuario_id": "USR_TEST_ELEVACION_01",
  "estado": "vulneracion_detectada",
  "vulneracion_detectada": true,
  "accion": "revocar_permisos",
  "mensaje": "Se ha presentado una vulneración: el último cambio de rol se realizó desde una IP distinta a la habitual del usuario. Se procederá a revocar los permisos.",
  "ip_habitual": "190.24.55.12",
  "ip_ultimo_cambio": "200.89.120.45",
  "total_eventos_analizados": 4,
  "incidente_registrado": true,
  "incidente_log_id": "8a3c0e0e-e218-486c-ae6a-d0c2adfc9525",
  "ultimo_cambio": {
    "identificador": "cambio-rol-1790454529",
    "ip_origen": "200.89.120.45",
    "fecha_creacion": "2026-09-26T15:28:50.647234+00:00",
    "detalle": {
      "rol_anterior": "CONSULTA",
      "rol_nuevo": "ADMIN"
    }
  }
}
```

#### Caso 2: Actividad Normal (Cambio de rol desde la IP habitual)
```json
{
  "usuario_id": "USR_TEST_ELEVACION_01",
  "estado": "sin_cambios",
  "vulneracion_detectada": false,
  "accion": null,
  "mensaje": "No hubo cambios: el último cambio de rol se realizó desde la IP habitual del usuario.",
  "ip_habitual": "190.24.55.12",
  "ip_ultimo_cambio": "190.24.55.12",
  "total_eventos_analizados": 3
}
```

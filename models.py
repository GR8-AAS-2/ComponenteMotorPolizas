from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Poliza(db.Model):
    __tablename__ = "polizas"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    numero_poliza = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # Datos del Titular / Tomador
    titular = db.Column(db.String(150), nullable=False)
    tipo_documento = db.Column(db.String(10), default="CC", nullable=False)
    documento_identidad = db.Column(db.String(30), nullable=False)
    email_titular = db.Column(db.String(120), nullable=True)
    telefono_titular = db.Column(db.String(25), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    ciudad = db.Column(db.String(80), nullable=True)

    # Datos del Seguro
    ramo = db.Column(db.String(60), nullable=False)
    tipo_cobertura = db.Column(db.String(100), nullable=False)
    monto_asegurado = db.Column(db.Numeric(14, 2), nullable=False)
    prima_mensual = db.Column(db.Numeric(10, 2), nullable=False)
    deducible = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)

    # Vigencia y Facturación
    fecha_inicio_vigencia = db.Column(db.Date, nullable=False)
    fecha_fin_vigencia = db.Column(db.Date, nullable=False)
    frecuencia_pago = db.Column(db.String(20), default="MENSUAL", nullable=False)
    metodo_pago = db.Column(db.String(30), default="DEBITO_AUTOMATICO", nullable=False)

    # Estado y Asesor
    estado = db.Column(db.String(20), default="ACTIVA", nullable=False)
    agente_codigo = db.Column(db.String(20), nullable=True)
    agente_nombre = db.Column(db.String(120), nullable=True)
    beneficiarios = db.Column(db.Text, nullable=True)

    # Auditoría del Registro
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "numero_poliza": self.numero_poliza,
            "titular": self.titular,
            "tipo_documento": self.tipo_documento,
            "documento_identidad": self.documento_identidad,
            "email_titular": self.email_titular,
            "telefono_titular": self.telefono_titular,
            "direccion": self.direccion,
            "ciudad": self.ciudad,
            "ramo": self.ramo,
            "tipo_cobertura": self.tipo_cobertura,
            "monto_asegurado": float(self.monto_asegurado) if self.monto_asegurado is not None else None,
            "prima_mensual": float(self.prima_mensual) if self.prima_mensual is not None else None,
            "deducible": float(self.deducible) if self.deducible is not None else None,
            "fecha_inicio_vigencia": self.fecha_inicio_vigencia.isoformat() if self.fecha_inicio_vigencia else None,
            "fecha_fin_vigencia": self.fecha_fin_vigencia.isoformat() if self.fecha_fin_vigencia else None,
            "frecuencia_pago": self.frecuencia_pago,
            "metodo_pago": self.metodo_pago,
            "estado": self.estado,
            "agente_codigo": self.agente_codigo,
            "agente_nombre": self.agente_nombre,
            "beneficiarios": self.beneficiarios,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_actualizacion": self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
        }

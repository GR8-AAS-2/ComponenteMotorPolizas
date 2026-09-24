"""
Script para poblar la base de datos PostgreSQL con 50 pólizas de prueba enriquecidas.
Uso:
    python seed_data.py
"""
import os
from sqlalchemy import text
from app import create_app
from models import db, Poliza

def seed():
    app = create_app()
    with app.app_context():
        print("🛠️  Iniciando carga de datos en la base de datos...")
        db.create_all()

        sql_file = os.path.join(os.path.dirname(__file__), "seed.sql")
        if os.path.exists(sql_file):
            print(f"📄 Leyendo sentencias desde '{sql_file}'...")
            with open(sql_file, "r", encoding="utf-8") as f:
                sql_content = f.read()

            try:
                # Ejecutar script SQL directamente en PostgreSQL
                db.session.execute(text(sql_content))
                db.session.commit()
                total = Poliza.query.count()
                print(f"\n✅ Carga exitosa: {total} pólizas registradas en la base de datos.\n")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error al ejecutar script de seed: {e}\n")
        else:
            print(f"❌ No se encontró el archivo '{sql_file}'")

if __name__ == "__main__":
    seed()

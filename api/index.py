import sys
import os

# Asegurar que el directorio raíz esté en sys.path para importar app, models, config, etc.
DIRECTORIO_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if DIRECTORIO_RAIZ not in sys.path:
    sys.path.insert(0, DIRECTORIO_RAIZ)

from app import app

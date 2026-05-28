import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.extraccion import extraer_desde_pdf
from modules.database import insertar_estudiantes
from config.settings import DOWNLOAD_DIR

def reparse_and_update():
    pdf_path = os.path.join(DOWNLOAD_DIR, "impresion.pdf")
    if os.path.exists(pdf_path):
        print("Leyendo PDF existente para actualizar jornada y titulares...")
        estudiantes = extraer_desde_pdf(pdf_path, "estudiantes")
        if estudiantes:
            print(f"Extrayendo {len(estudiantes)} estudiantes...")
            res = insertar_estudiantes(estudiantes)
            print("Base de datos actualizada:", res)
        else:
            print("No se encontraron estudiantes en el PDF.")
    else:
        print("No se encontro el PDF.")

if __name__ == "__main__":
    reparse_and_update()

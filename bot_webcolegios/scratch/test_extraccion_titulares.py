import glob
from modules.extraccion import extraer_titulares_de_pdfs

rutas = glob.glob("downloads/titulares_grado_*.pdf")
print(f"Buscando en {len(rutas)} PDFs")
titulares = extraer_titulares_de_pdfs(rutas)

print("\n--- TITULARES EXTRAIDOS ---")
for nombre, datos in titulares.items():
    print(f"Nombre: '{nombre}'")
    print(f"Grado: '{datos.get('grado_titular')}'")
    print(f"Curso: '{datos.get('curso_titular')}'")
    print("-" * 20)

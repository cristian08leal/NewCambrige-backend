import re
import pdfplumber

with pdfplumber.open("downloads/test_docentes.pdf") as pdf:
    texto = "".join(p.extract_text() or "" for p in pdf.pages)

print("--- TEXTO CRUDO ---")
print(texto)
print("\n--- TEST REGEX ---")

PATRON_DOCENTE = re.compile(
    r'^\s*(?:(\d+)\s+)?(\d{5,15})\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]+?)\s*$',
    re.IGNORECASE | re.MULTILINE
)
encontrados = PATRON_DOCENTE.findall(texto)
print(f"Matches: {len(encontrados)}")
for m in encontrados[:5]:
    print(m)

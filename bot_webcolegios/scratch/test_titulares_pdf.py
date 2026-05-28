import pdfplumber
import glob

pdfs = glob.glob("downloads/titulares_grado_*.pdf")
if pdfs:
    print(f"Reading {pdfs[0]}")
    with pdfplumber.open(pdfs[0]) as pdf:
        text = pdf.pages[0].extract_text()
        print("--- FIRST 500 CHARACTERS ---")
        print(text[:500])
        print("----------------------------")
else:
    print("No PDFs found")

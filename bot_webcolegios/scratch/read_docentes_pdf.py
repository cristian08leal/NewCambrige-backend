import pdfplumber

with pdfplumber.open("downloads/test_docentes.pdf") as pdf:
    print(f"Total páginas: {len(pdf.pages)}")
    for i, page in enumerate(pdf.pages[:3]):
        print(f"\n{'='*60}")
        print(f"PÁGINA {i+1}")
        print('='*60)
        text = page.extract_text()
        if text:
            print(text[:3000])
        else:
            print("(Sin texto)")

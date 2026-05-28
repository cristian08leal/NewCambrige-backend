import pdfplumber
import sys

def dump():
    text = ""
    with pdfplumber.open(sys.argv[1]) as pdf:
        for p in pdf.pages:
            text += p.extract_text() + "\n"
    print(text)

if __name__ == '__main__':
    dump()

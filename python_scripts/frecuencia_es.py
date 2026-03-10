from pypdf import PdfReader
from collections import Counter
import re
import unicodedata

def normalizar(t):
    t = t.lower()
    return ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')

def escanear_libro(path):
    reader = PdfReader(path)
    conteo = Counter()
    # Escaneamos solo las primeras 50 páginas para no saturar
    for i in range(min(50, len(reader.pages))):
        texto = reader.pages[i].extract_text()
        palabras = re.findall(r'\b[a-z]{5,}\b', normalizar(texto))
        conteo.update(palabras)
    
    print(f"--- TOP 20 PALABRAS ENCONTRADAS EN {path} ---")
    for word, freq in conteo.most_common(20):
        print(f"{word}: {freq}")

if __name__ == "__main__":
    escanear_libro("Deuda Graeber.pdf") # Ajusta el nombre si es necesario
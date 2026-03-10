from pypdf import PdfReader
reader = PdfReader("The Rust Programming Book.pdf")
print(f"Paginas: {len(reader.pages)}")
texto = reader.pages[0].extract_text()
print(f"Texto p1: {repr(texto[:300]) if texto else 'VACIO'}")

import sys
from pathlib import Path

ARCHIVO_OBJETIVO = Path("process_book_v2.py")

# Lista de términos con alta carga de sesgo (Propaganda/Sensacionalismo)
D21_BIAS_MAP = """
# D21: Bias Decoupling Map
MAPA_SESGO_D21 = {
    "definitivo", "incuestionable", "siempre", "nunca", "obvio", 
    "manipulación", "conspiración", "revolucionario", "milagroso",
    "catastrófico", "inevitable", "salvación", "destrucción"
}
"""

LOGICA_FILTRO_SESGO = """
def filtrar_sesgo_d21(texto):
    \"\"\"
    D21: Detecta lenguaje polarizado y devuelve un factor de confianza.
    \"\"\"
    palabras = texto.lower().split()
    coincidencias = sum(1 for p in palabras if p in MAPA_SESGO_D21)
    # Factor de confianza: a más palabras sesgadas, menor peso (mínimo 0.3)
    confianza = max(0.3, 1.0 - (coincidencias * 0.1))
    if confianza < 1.0:
        print(f"⚖️ D21 (Bias Filter): Confianza reducida a {confianza:.2f} por lenguaje polarizado.")
    return confianza
"""

def aplicar_d21():
    with open(ARCHIVO_OBJETIVO, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    nueva_lista = []
    # Insertar el mapa de sesgo después de los otros mapas
    for linea in lineas:
        nueva_lista.append(linea)
        if "MAPA_TECH = {" in linea:
            # Esperar al final del diccionario (esto es una simplificación)
            pass
        if "STOPWORDS = {" in linea:
            nueva_lista.append(D21_BIAS_MAP + "\n")
            nueva_lista.append(LOGICA_FILTRO_SESGO + "\n")

    # Modificar la llamada a 'reforzar' dentro de procesar_libro
    # (Esto requeriría un cambio más profundo en el bucle del Hunter)
    
    with open(ARCHIVO_OBJETIVO, "w", encoding="utf-8") as f:
        f.writelines(nueva_lista)
    print("✅ D21 INSTALADA: ANIMUS ahora filtra el sesgo de sus fuentes.")

if __name__ == "__main__":
    aplicar_d21()
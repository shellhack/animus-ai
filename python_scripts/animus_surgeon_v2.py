import sys
from pathlib import Path

ARCHIVO_OBJETIVO = Path("process_book_v2.py")

# La nueva lógica que inyectaremos
NUEVA_LOGICA_REFORZAR = """
def reforzar(d, clave, valor):
    \"\"\"
    D05: Refuerzo Logarítmico Autónomo. 
    Sustituye el techo lineal por rendimientos decrecientes.
    \"\"\"
    import math
    valor_actual = d.get(clave, 0.0)
    # Factor de atenuación: a mayor peso, menor impacto del nuevo dato
    atenuacion = 1 / (1 + math.log1p(valor_actual))
    nuevo_total = valor_actual + (valor * atenuacion)
    d[clave] = round(nuevo_total, 4)
"""

def ejecutar_cirugia():
    if not ARCHIVO_OBJETIVO.exists():
        print("❌ Error: No se encuentra process_book_v2.py")
        return

    with open(ARCHIVO_OBJETIVO, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    nueva_lista = []
    saltar = False
    encontrada = False
    
    for linea in lineas:
        # Buscamos tu firma exacta: def reforzar(d, clave, valor):
        if "def reforzar(d, clave, valor):" in linea:
            nueva_lista.append(NUEVA_LOGICA_REFORZAR)
            saltar = True
            encontrada = True
            continue
        
        # Dejamos de saltar cuando encontramos la siguiente función o una línea vacía después del bloque
        if saltar and (linea.startswith("def ") or (linea.strip() == "" and encontrada)):
            saltar = False
        
        if not saltar:
            nueva_lista.append(linea)
    
    if encontrada:
        with open(ARCHIVO_OBJETIVO, "w", encoding="utf-8") as f:
            f.writelines(nueva_lista)
        print("✅ MUTACIÓN COMPLETADA: Lógica logarítmica inyectada con éxito.")
    else:
        print("❌ No se encontró la firma 'def reforzar(d, clave, valor):'. Verifica el archivo.")

if __name__ == "__main__":
    ejecutar_cirugia()
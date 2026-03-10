import sys
import re
from pathlib import Path

ARCHIVO_OBJETIVO = Path("process_book_v2.py")

NUEVA_FUNCION_REFORZAR = """
def reforzar(diccionario, clave, incremento):
    \"\"\"
    D05: Refuerzo Logarítmico (Rendimientos decrecientes).
    Evita la hipertrofia de tokens y mantiene la flexibilidad mental.
    \"\"\"
    import math
    valor_actual = diccionario.get(clave, 0.0)
    # Factor de atenuación: a mayor valor, menor impacto del incremento
    atenuacion = 1 / (1 + math.log1p(valor_actual))
    nuevo_valor = valor_actual + (incremento * atenuacion)
    diccionario[clave] = round(nuevo_valor, 4)
"""

def ejecutar_mutacion():
    if not ARCHIVO_OBJETIVO.exists():
        print("❌ Error: No se encuentra process_book_v2.py")
        return

    with open(ARCHIVO_OBJETIVO, "r", encoding="utf-8") as f:
        contenido = f.read()

    # Buscamos la función 'reforzar' vieja y su cuerpo
    # Esta regex busca desde 'def reforzar' hasta el final de su bloque indentado
    patron_viejo = r"def reforzar\(diccionario, clave, incremento\):.*?\n(?!\s)"
    
    if "def reforzar" in contenido:
        # Reemplazo quirúrgico
        # Nota: Usamos una técnica más simple si la regex falla por indentación
        lineas = contenido.splitlines()
        nueva_lista = []
        saltar = False
        
        for linea in lineas:
            if linea.startswith("def reforzar(diccionario, clave, incremento):"):
                saltar = True
                nueva_lista.append(NUEVA_FUNCION_REFORZAR)
                continue
            if saltar and (linea.startswith("def ") or (linea.strip() == "" and not saltar)):
                saltar = False
            if not saltar:
                nueva_lista.append(linea)
        
        with open(ARCHIVO_OBJETIVO, "w", encoding="utf-8") as f:
            f.write("\n".join(nueva_lista))
        
        print("✅ MUTACIÓN EXITOSA: ANIMUS ha reescrito su propia lógica de aprendizaje.")
    else:
        print("❌ No se encontró la función 'reforzar' para mutar.")

if __name__ == "__main__":
    ejecutar_mutacion()
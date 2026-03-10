import json
import os

MAPA_FILE = "process_book_v2.py" # El mutador leerá el script principal

def inyectar_conocimiento_al_mapa(nuevo_token, categoria):
    """
    Permite que ANIMUS sugiera y añada palabras clave al 
    MAPA_SABIDURIA o MAPA_TECH directamente en el código.
    """
    with open(MAPA_FILE, 'r', encoding='utf-8') as f:
        lineas = f.readlines()

    with open(MAPA_FILE, 'w', encoding='utf-8') as f:
        for linea in lineas:
            f.write(linea)
            # Buscamos la definición del mapa para insertar la nueva palabra
            if f'MAPA_{categoria} = {{' in linea:
                f.write(f'    "{nuevo_token}": "{nuevo_token}",\n')
                print(f"✨ MUTACIÓN: Añadido '{nuevo_token}' al MAPA_{categoria}")

# Ejemplo de uso que ANIMUS podrá disparar solo:
# inyectar_conocimiento_al_mapa("obsolescencia", "TECH")
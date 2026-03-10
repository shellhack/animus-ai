import json
from pathlib import Path

def analizar_resistencia_bilingue():
    with open('memoria_business.json', 'r', encoding='utf-8') as f:
        mem = json.load(f)
    
    conexiones = mem.get('conexiones', {})
    fuentes = set()
    for k in conexiones:
        fuentes.add(k.split('_')[0])
    
    print(f"📊 FUENTES DETECTADAS: {len(fuentes)}")
    print(f"🧐 ¿Existe 'taleb_es'?: {'SÍ' if 'taleb' in fuentes else 'NO (se fusionó)'}")
    print(f"🧐 ¿Existe 'meadows_es'?: {'SÍ' if 'meadows' in fuentes else 'NO (se fusionó)'}")
    
    # Verificar si el vocabulario español creció realmente
    lenguaje = mem.get('lenguaje', {})
    print(f"🌐 Vocabulario ES: {len(lenguaje)} palabras")

if __name__ == "__main__":
    analizar_resistencia_bilingue()
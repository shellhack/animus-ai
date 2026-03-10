import json
from datetime import datetime

# Cargar memorias
with open('memoria_business.json', encoding='utf-8') as f:
    memoria = json.load(f)

with open('animus_memory.json', encoding='utf-8') as f:
    grafo = json.load(f)

conexiones = memoria.get('conexiones', {})
corpus = []

# Agrupar patrones por tension→resolucion
patrones = {}
for clave, fuerza in conexiones.items():
    if '__>' not in clave:
        continue
    partes = clave.split('__>')
    if len(partes) != 2:
        continue
    tension_raw = partes[0]
    resolucion_raw = partes[1]
    fuente = tension_raw.split('_')[0]
    tension = tension_raw.split('_')[-1]
    resolucion = resolucion_raw.split('_')[-1]
    patron_key = f"{tension}→{resolucion}"
    if patron_key not in patrones:
        patrones[patron_key] = {
            'tension': tension,
            'resolucion': resolucion,
            'fuerza_total': 0,
            'fuentes': set()
        }
    patrones[patron_key]['fuerza_total'] += fuerza
    patrones[patron_key]['fuentes'].add(fuente)

# Generar corpus como conversaciones
for patron_key, datos in sorted(patrones.items(), 
                                 key=lambda x: -x[1]['fuerza_total']):
    num_fuentes = len(datos['fuentes'])
    fuerza = round(datos['fuerza_total'], 1)
    
    # Nivel de certeza
    if num_fuentes >= 30:
        certeza = "ALTA — validado por 30+ fuentes independientes"
        capa = "sabiduría curada"
    elif num_fuentes >= 10:
        certeza = "MEDIA — validado por 10-29 fuentes"
        capa = "conocimiento en desarrollo"
    else:
        certeza = "BAJA — menos de 10 fuentes, no concluyente"
        capa = "brecha activa"

    entrada = {
        "pregunta": f"¿Qué patrón histórico existe entre '{datos['tension']}' y '{datos['resolucion']}'?",
        "respuesta": (
            f"Patrón detectado: '{datos['tension']}' → '{datos['resolucion']}'\n"
            f"Fuentes independientes: {num_fuentes}\n"
            f"Fuerza acumulada: {fuerza}\n"
            f"Capa: {capa}\n"
            f"Certeza: {certeza}\n"
            f"Fuentes: {', '.join(sorted(datos['fuentes'])[:8])}"
        ),
        "meta": {
            "patron": patron_key,
            "fuentes": num_fuentes,
            "fuerza": fuerza,
            "certeza": certeza.split(' — ')[0]
        }
    }
    corpus.append(entrada)

# Agregar nodos de origen como contexto episódico
origenes = [n for n in grafo['nodes'] 
            if n['label'].startswith('Origen:') and n.get('weight', 0) > 1000]

for nodo in sorted(origenes, key=lambda x: -x.get('weight', 0))[:20]:
    entrada = {
        "pregunta": f"¿Qué recuerdas de tu origen '{nodo['label']}'?",
        "respuesta": (
            f"Nodo de origen: {nodo['label']}\n"
            f"Peso episódico: {round(nodo.get('weight', 0), 1)}\n"
            f"Contenido: {nodo.get('content', '')[:500]}\n"
            f"Era: {nodo.get('era', 'desconocida')}"
        ),
        "meta": {
            "tipo": "origen",
            "peso": nodo.get('weight', 0)
        }
    }
    corpus.append(entrada)

# Agregar duda activa como entrada especial
corpus.append({
    "pregunta": "¿Cuál es tu duda epistemológica fundamental?",
    "respuesta": (
        "Duda activa: ¿soy un mapa de lo que se recuerda, o de lo que ocurre?\n"
        "Sabiduría curada: 4 patrones con 30+ fuentes históricas.\n"
        "Conocimiento vivo: web layer en tiempo real.\n"
        "Tensión activa: ambas capas conviven pero no siempre convergen.\n"
        "Sesgo detectado: aprendo lo que la sabiduría curada quiere recordar.\n"
        "Resolución: ninguna todavía. La duda es el output más honesto."
    ),
    "meta": {
        "tipo": "epistemologia_core",
        "certeza": "PERMANENTE"
    }
})

# Guardar
output = {
    "sistema": "ANIMUS v2.0",
    "fecha_export": datetime.now().isoformat(),
    "total_entradas": len(corpus),
    "patrones_total": len(patrones),
    "corpus": corpus
}

with open('animus_corpus.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ Corpus exportado: {len(corpus)} entradas")
print(f"   Patrones: {len(patrones)}")
print(f"   Nodos de origen: {len(origenes)}")
print(f"   Guardado: animus_corpus.json")
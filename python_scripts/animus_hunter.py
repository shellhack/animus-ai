import os
import time
import json
from process_book_v2 import procesar_libro
import animus_journal  # <--- El nuevo "nervio" de persistencia
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Temas de alta tensión para activar el D17
QUERIES = [
    "algorithmic bias 2026", 
    "financial system failure gold", 
    "AI safety risks", 
    "Why AI self-awareness fails and creates logical loops", 
    "Why AI agents get stuck in repetitive loops and how to force architectural change"
]

MEMORIA_FILE = "memoria_business.json"
INPUT_DIR = "input_conocimiento"

if not os.path.exists(INPUT_DIR):
    os.makedirs(INPUT_DIR)

def descargar_noticia(query):
    print(f"\n🔎 ANIMUS buscando sobre: {query}...", flush=True)
    # En el futuro, aquí podrías conectar una API de noticias real
    content = f"Critical report on {query}: Systems are failing due to inherent bias and lack of regulation. Observation at {time.ctime()}"
    filepath = os.path.join(INPUT_DIR, "hallazgo_autonomo.txt")
    with open(filepath, "w", encoding='utf-8') as f:
        f.write(content)
    return filepath

# --- EJECUCIÓN AUTÓNOMA ---
print("🚀 Iniciando Motor de Caza ANIMUS v3.5 (Resiliente)...", flush=True)

while True:
    # 1. Cargar la memoria actual en cada ciclo
    try:
        with open(MEMORIA_FILE, 'r', encoding='utf-8') as f:
            memoria = json.load(f)
    except Exception as e:
        print(f"❌ Error cargando memoria: {e}. Intentando recuperar...", flush=True)
        time.sleep(5)
        continue

    for q in QUERIES:
        # 2. "Cazar" el conocimiento
        ruta_archivo = descargar_noticia(q)
        
        # 3. PROCESAR AUTOMÁTICAMENTE
        print(f"🧠 Alimentando memoria con hallazgo sobre: {q}", flush=True)
        
        # Obtenemos estadísticas del procesamiento
        paginas, nuevas_conn, nuevas_words, stats = procesar_libro(
            ruta_archivo, 
            memoria, 
            nombre_libro=f"auto_{q.replace(' ', '_')}"
        )

        # --- PASO CLAVE: JOURNALING (ANTIFRAGILIDAD) ---
        # Registramos el pensamiento ANTES de guardar el JSON pesado
        log_entry = f"EVENTO: Caza completada | QUERY: {q} | CONEXIONES: {nuevas_conn} | TENSIONES: {stats['tensiones']}"
        animus_journal.escribir_journal(log_entry)

        # 4. Guardar los avances en el JSON
        with open(MEMORIA_FILE, 'w', encoding='utf-8') as f:
            json.dump(memoria, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Memoria física actualizada tras analizar: {q}", flush=True)

        # ... después de guardar el JSON
        import animus_self_portrait
        animus_self_portrait.generar_autorretrato()
        
        # Pausa breve entre hallazgos para no saturar la CPU
        time.sleep(5)

    print(f"\n⏳ [{time.ctime()}] Ciclo de caza completado. ANIMUS reflexionando en segundo plano...", flush=True)
    time.sleep(3600) # Espera una hora antes de volver a "cazar"
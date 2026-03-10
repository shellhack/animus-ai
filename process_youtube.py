"""
ANIMUS — YouTube Transcript Processor
Busca videos por tema en YouTube, descarga transcripciones y las alimenta
al grafo de sabiduría de ANIMUS usando el mismo pipeline de process_book_v2.py

Usage:
    python process_youtube.py --tema "crisis financiera latinoamerica" --max 10
    python process_youtube.py --tema "regulacion inteligencia artificial" --max 5 --memoria memoria_business.json
    python process_youtube.py --temas temas.txt --max 8

Temas recomendados para ANIMUS:
    - "crisis financiera latinoamerica"
    - "regulacion inteligencia artificial"
    - "colapso institucional"
    - "algoritmos fracaso sistemas"
    - "economia dominicana"
    - "AI regulation failure"
    - "systemic risk algorithm"
"""

import json
import re
import sys
import argparse
import unicodedata
from pathlib import Path
from datetime import datetime

try:
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
except ImportError:
    print("Error: youtube-transcript-api no instalado.")
    print("Ejecuta: pip install youtube-transcript-api --break-system-packages")
    sys.exit(1)

try:
    from youtubesearchpython import VideosSearch
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False

# ──────────────────────────────────────────────────────────────────────────────
# VOCABULARIO (mismo que process_book_v2.py)
# ──────────────────────────────────────────────────────────────────────────────

MAPA_SABIDURIA = {
    "orgullo": "failure", "soberbia": "failure", "necedad": "failure",
    "ignorancia": "failure", "error": "failure", "vicio": "failure",
    "pereza": "poverty", "mentira": "corruption", "engaño": "fraud",
    "codicia": "gap", "avaricia": "gap", "ira": "crisis",
    "violencia": "collapse", "guerra": "crisis", "conflicto": "crisis",
    "derrota": "failure", "miedo": "threat", "dolor": "crisis",
    "muerte": "collapse", "decadencia": "collapse", "desorden": "crisis",
    "caos": "collapse", "obstáculo": "failure", "obstaculo": "failure",
    "pobreza": "poverty", "miseria": "poverty", "injusticia": "inequality",
    "opresión": "inequality", "opresion": "inequality", "tiranía": "collapse",
    "tirania": "collapse", "deuda": "debt", "credito": "incentive",
    "dinero": "algorithm", "moneda": "algorithm", "mercado": "regulation",
    "sabiduría": "education", "sabiduria": "education", "razón": "algorithm",
    "razon": "algorithm", "virtud": "reform", "disciplina": "developed",
    "justicia": "reform", "humildad": "cooperation", "conocimiento": "discovered",
    "aprendizaje": "education", "inteligencia": "algorithm", "estrategia": "algorithm",
    "equilibrio": "solution", "ley": "regulation", "principio": "regulation",
    "integridad": "regulation", "liderazgo": "cooperation",
}

MAPA_TECH = {
    "fallo": "failure", "falla": "failure", "error": "failure", "bug": "failure",
    "colapso": "collapse", "crash": "collapse", "obsolescencia": "obsolescence",
    "latencia": "gap", "limitación": "limitation", "limitacion": "limitation",
    "vulnerabilidad": "vulnerability", "brecha": "gap", "fragmentación": "gap",
    "sesgo": "inequality", "bias": "inequality", "alucinación": "fraud",
    "alucinacion": "fraud", "opacidad": "corruption", "dependencia": "addiction",
    "procesador": "algorithm", "memoria": "developed", "optimización": "optimized",
    "optimizacion": "optimized", "escalabilidad": "scaled", "arquitectura": "framework",
    "semiconductor": "innovation", "algoritmo": "algorithm", "algorithm": "algorithm",
    "aprendizaje": "education", "entrenamiento": "training", "transformer": "innovation",
    "datos": "algorithm", "dataset": "algorithm", "regularización": "regulation",
    "regularizacion": "regulation", "emergencia": "innovation", "emergente": "innovation",
    "adaptativo": "transformed", "recursivo": "algorithm", "autoconciencia": "discovered",
    "evolución": "developed", "evolucion": "developed", "mejora": "developed",
    "iteración": "algorithm", "iteracion": "algorithm",
    # Tokens específicos para contenido sobre IA y energía
    "consumo": "gap", "energía": "gap", "energia": "gap", "electricidad": "gap",
    "datacenter": "failure", "infraestructura": "framework", "regulación": "regulation",
    "regulacion": "regulation", "inversión": "incentive", "inversion": "incentive",
    "rentabilidad": "gap", "pérdidas": "failure", "perdidas": "failure",
    "subsidio": "corruption", "monopolio": "monopoly", "censura": "corruption",
    "privacidad": "vulnerability", "vigilancia": "corruption",
}

STOPWORDS = {
    "para", "como", "pero", "más", "cuando", "todo", "esta", "este",
    "algo", "bien", "solo", "muy", "cada", "mismo", "puede", "tiene",
    "dice", "dijo", "años", "entre", "sobre", "desde", "hasta", "también",
    "porque", "había", "estar", "tienen", "hacer", "después", "antes",
    "ahora", "donde", "siempre", "nunca", "bueno", "pues", "vamos",
    "aquí", "allí", "hemos", "ellos", "ellas", "nosotros", "vosotros",
    "esto", "esos", "esas", "ello", "cuyo", "cuyos", "cual", "cuales",
    "sino", "aunque", "mientras", "durante", "mediante", "través",
}

MAPA = {**MAPA_SABIDURIA, **MAPA_TECH}

PALABRAS_TENSION = set(k for k, v in MAPA.items() if v in {
    "failure", "poverty", "corruption", "fraud", "gap", "crisis", "collapse",
    "inequality", "vulnerability", "limitation", "debt", "addiction",
    "obsolescence", "monopoly",
})

PALABRAS_RESOLUCION = set(k for k, v in MAPA.items() if v in {
    "education", "cooperation", "developed", "reform", "regulation", "algorithm",
    "discovered", "incentive", "solution", "prevention", "innovation", "transformed",
    "training", "framework", "optimized", "scaled",
})


# ──────────────────────────────────────────────────────────────────────────────
# UTILIDADES
# ──────────────────────────────────────────────────────────────────────────────

def normalizar(t):
    t = t.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', t)
                   if unicodedata.category(c) != 'Mn')


def reforzar(d, clave, valor):
    import math
    actual = d.get(clave, 0.0)
    atenuacion = 1 / (1 + math.log1p(actual))
    d[clave] = round(actual + (valor * atenuacion), 4)


def limpiar_nombre(texto):
    """Convierte un tema en nombre válido para clave de memoria."""
    nombre = re.sub(r'[^a-zA-Z0-9]', '_', texto.lower())
    return nombre[:25].strip('_')


# ──────────────────────────────────────────────────────────────────────────────
# BÚSQUEDA DE VIDEOS
# ──────────────────────────────────────────────────────────────────────────────

def buscar_videos_youtube(tema, max_videos=10):
    import subprocess, json
    try:
        cmd = [
            "yt-dlp",
            f"ytsearch{max_videos}:{tema}",
            "--dump-json",
            "--no-download",
            "--quiet"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                videos.append({
                    'id': data['id'],
                    'titulo': data['title'],
                    'canal': data.get('uploader', 'desconocido'),
                    'duracion': data.get('duration_string', '?'),
                })
            except Exception:
                continue
        return videos
    except Exception as e:
        print(f"  Error en búsqueda: {e}")
        return []


def obtener_transcripcion(video_id, idiomas=['es', 'en', 'es-419', 'es-ES']):
    """Descarga transcripción de un video de YouTube."""
    try:
        ytt = YouTubeTranscriptApi(cookies="youtube_cookies.txt")
        transcript = ytt.fetch(video_id, languages=idiomas)
        texto = ' '.join(t.text for t in transcript)
        return texto
    except Exception:
        try:
            ytt = YouTubeTranscriptApi(cookies="youtube_cookies.txt")
            lista = ytt.list(video_id)
            for t in lista:
                try:
                    fetched = t.fetch()
                    return ' '.join(item.text for item in fetched)
                except Exception:
                    continue
        except Exception:
            pass
        return None


# ──────────────────────────────────────────────────────────────────────────────
# PROCESAMIENTO
# ──────────────────────────────────────────────────────────────────────────────

def procesar_transcripcion(texto, memoria, nombre_fuente):
    """Procesa una transcripción y alimenta el grafo de ANIMUS."""
    chunk_size = 800
    chunks = [texto[i:i+chunk_size] for i in range(0, len(texto), chunk_size)]

    nuevas_conn = 0
    tensiones_total = 0
    resoluciones_total = 0

    for chunk in chunks:
        palabras_raw = re.findall(r'[a-záéíóúüña-z]{4,}', chunk.lower())
        palabras_set = set()
        for p in palabras_raw:
            p_norm = normalizar(p)
            if p_norm not in STOPWORDS:
                palabras_set.add(p_norm)

        tensiones = [p for p in palabras_set if p in PALABRAS_TENSION]
        resoluciones = [p for p in palabras_set if p in PALABRAS_RESOLUCION]

        tensiones_total += len(tensiones)
        resoluciones_total += len(resoluciones)

        for t in tensiones:
            token = MAPA[t]
            reforzar(memoria["problemas"], f"{nombre_fuente}_{token}", 1.5)

        for r in resoluciones:
            token = MAPA[r]
            reforzar(memoria["soluciones"], f"{nombre_fuente}_{token}", 1.5)

        if tensiones and resoluciones:
            for t in tensiones[:4]:
                for r in resoluciones[:4]:
                    clave = f"{nombre_fuente}_{MAPA[t]}__>{nombre_fuente}_{MAPA[r]}"
                    if clave not in memoria["conexiones"]:
                        nuevas_conn += 1
                    reforzar(memoria["conexiones"], clave, 1.2)

        # Vocabulario
        for palabra in palabras_set:
            if palabra in MAPA:
                token = MAPA[palabra]
                reforzar(memoria["lenguaje"], f"{palabra}__={token}", 1.0)

    return nuevas_conn, tensiones_total, resoluciones_total


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ANIMUS YouTube Transcript Processor")
    parser.add_argument("--tema", help="Tema a buscar en YouTube")
    parser.add_argument("--temas", help="Archivo .txt con un tema por línea")
    parser.add_argument("--ids", nargs="+", help="IDs de video específicos (ej: dQw4w9WgXcQ)")
    parser.add_argument("--max", type=int, default=10, help="Máximo de videos por tema (default: 10)")
    parser.add_argument("--memoria", default="memoria_business.json", help="Archivo de memoria ANIMUS")
    args = parser.parse_args()

    if not args.tema and not args.temas and not args.ids:
        parser.print_help()
        sys.exit(1)

    if not Path(args.memoria).exists():
        print(f"Error: {args.memoria} no encontrado.")
        sys.exit(1)

    with open(args.memoria, encoding="utf-8") as f:
        memoria = json.load(f)

    memoria.setdefault("problemas", {})
    memoria.setdefault("soluciones", {})
    memoria.setdefault("conexiones", {})
    memoria.setdefault("lenguaje", {})
    memoria.setdefault("fuentes_youtube", {})

    temas = []
    if args.tema:
        temas.append(args.tema)
    if args.temas and Path(args.temas).exists():
        with open(args.temas, encoding="utf-8") as f:
            temas.extend(line.strip() for line in f if line.strip())

    total_videos = 0
    total_conexiones = 0

    # Procesar por IDs directos
    if args.ids:
        print(f"\n🎬 Procesando {len(args.ids)} videos por ID...")
        for vid_id in args.ids:
            print(f"\n  📹 Video: {vid_id}")
            texto = obtener_transcripcion(vid_id)
            if not texto:
                print(f"  ❌ Sin transcripción disponible")
                continue
            nombre = f"yt_{vid_id[:8]}"
            conn, tens, reso = procesar_transcripcion(texto, memoria, nombre)
            memoria["fuentes_youtube"][vid_id] = {
                "procesado": datetime.now().isoformat(),
                "palabras": len(texto.split()),
                "conexiones": conn,
            }
            print(f"  ✅ {len(texto.split())} palabras | {tens} tensiones | {reso} resoluciones | {conn} conexiones nuevas")
            total_videos += 1
            total_conexiones += conn

    # Procesar por temas
    for tema in temas:
        print(f"\n🔍 Tema: '{tema}'")
        nombre_tema = limpiar_nombre(tema)

        videos = buscar_videos_youtube(tema, args.max)

        if not videos:
            print(f"  Sin resultados de búsqueda para este tema.")
            print(f"  Tip: usa --ids para pasar IDs de video directamente.")
            continue

        print(f"  Encontrados: {len(videos)} videos")

        for video in videos:
            vid_id = video['id']

            # Evitar reprocesar
            if vid_id in memoria["fuentes_youtube"]:
                print(f"  ⏭️  Ya procesado: {video['titulo'][:50]}")
                continue

            print(f"  📹 {video['titulo'][:60]}...")
            texto = obtener_transcripcion(vid_id)

            if not texto:
                print(f"  ❌ Sin transcripción")
                continue

            nombre = f"yt_{nombre_tema}_{vid_id[:6]}"
            conn, tens, reso = procesar_transcripcion(texto, memoria, nombre)

            memoria["fuentes_youtube"][vid_id] = {
                "titulo": video['titulo'],
                "canal": video['canal'],
                "tema": tema,
                "procesado": datetime.now().isoformat(),
                "palabras": len(texto.split()),
                "conexiones": conn,
            }

            print(f"  ✅ {len(texto.split())} palabras | {tens} tensiones | {reso} reso | {conn} conn nuevas")
            total_videos += 1
            total_conexiones += conn

    # Guardar
    memoria["ultima_actualizacion"] = datetime.now().isoformat()
    with open(args.memoria, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"✅ ANIMUS YouTube Processor completado")
    print(f"   Videos procesados:  {total_videos}")
    print(f"   Conexiones nuevas:  {total_conexiones}")
    print(f"   Fuentes YouTube:    {len(memoria['fuentes_youtube'])}")
    print(f"   Total conexiones:   {len(memoria['conexiones'])}")
    print(f"💾 Memoria guardada: {args.memoria}")


if __name__ == "__main__":
    main()

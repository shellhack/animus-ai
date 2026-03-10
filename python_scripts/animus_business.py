"""
ANIMUS Business — Agente detector de desequilibrios y patrones de resolución
El desequilibrio es la señal. La resolución es el objetivo emergente.
Sin objetivos externos. Sin supervisión. Solo tensión y contrapeso.
"""

import json
import time
import random
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────────────────────────────────────

FUENTES_SEMILLA = [
    "https://hbr.org",
    "https://www.economist.com",
    "https://www.reuters.com/business",
    "https://www.weforum.org/agenda",
    "https://www.mckinsey.com/insights",
    "https://techcrunch.com",
    "https://arxiv.org/list/econ/recent",
    "https://www.sciencedaily.com/news/computers_math/artificial_intelligence/",
    "https://www.bbc.com/news/business",
    "https://www.imf.org/en/News",
]

# Fuentes en español — para aprendizaje de lenguaje
FUENTES_ESPANOL = [
    "https://www.bbc.com/mundo/noticias",
    "https://elpais.com/economia",
    "https://www.expansion.com",
    "https://www.eleconomista.es",
    "https://www.reuters.com/es/",
]

# Corpus de texto español garantizado — para cuando las páginas web no tienen suficiente contenido
CORPUS_ESPANOL = [
    "La inflación es uno de los principales problemas económicos actuales. La política monetaria busca controlar la crisis inflacionaria mediante regulación del crédito y reforma fiscal. La corrupción y el fraude debilitan las instituciones democráticas.",
    "La ciberseguridad se ha convertido en una prioridad de inversión global. Las amenazas digitales representan un riesgo creciente para empresas y gobiernos. La innovación tecnológica es la principal herramienta de prevención.",
    "La desigualdad económica es una brecha que separa a ricos y pobres. La educación es fundamental para superar la pobreza. El desarrollo de políticas públicas efectivas requiere cooperación internacional.",
    "La pandemia reveló la fragilidad de los sistemas de salud. La vacuna fue el mayor avance científico para combatir la epidemia. La automatización del diagnóstico médico es una innovación que salva vidas.",
    "El desempleo y la recesión afectan a millones de personas. La reforma laboral busca reducir la escasez de empleo. La inversión en educación y tecnología es clave para la recuperación económica.",
    "La sequía y las inundaciones son consecuencias del cambio climático. La energía renovable es la solución para reducir las emisiones contaminantes. La regulación ambiental y la cooperación global son esenciales.",
    "La corrupción política es un obstáculo para el desarrollo. La reforma institucional y la educación cívica son herramientas de prevención. La transparencia y la regulación reducen el fraude en el sector público.",
    "La deuda pública es un déficit que limita el crecimiento económico. La política fiscal y la reforma tributaria buscan reducir el déficit. La innovación en finanzas digitales ofrece nuevas soluciones de inversión.",
    "El agotamiento laboral afecta la productividad y la salud mental. Las iniciativas de bienestar empresarial son un marco de solución emergente. La regulación del tiempo de trabajo es una política necesaria.",
    "La desigualdad tecnológica crea una brecha digital entre países. La educación digital y la cooperación internacional son claves para el desarrollo. La inversión en infraestructura tecnológica reduce la pobreza digital.",
    "La contaminación ambiental es un colapso del equilibrio ecológico. La amenaza del cambio climático requiere algoritmos de predicción y soluciones de descubrimiento científico. La limitación de emisiones es una iniciativa global urgente.",
    "El fracaso de las instituciones genera colapso social y económico. El algoritmo de detección de fraude es un descubrimiento tecnológico clave. La iniciativa regulatoria busca superar la limitación de los sistemas actuales.",
    "La amenaza del desempleo tecnológico requiere iniciativas de reconversión laboral. El algoritmo de automatización tiene limitaciones que el descubrimiento científico busca superar. La contaminación digital es un colapso de la privacidad.",
    "El cambio climático genera inundaciones, sequías y pérdidas económicas masivas. La transición energética hacia fuentes renovables es urgente. La reforestación y la reducción de emisiones son soluciones comprobadas.",
    "La recesión económica provoca desempleo masivo y quiebras empresariales. La recuperación requiere inversión pública, reforma fiscal y cooperación internacional. La tecnología digital acelera la transformación productiva.",
    "La pandemia evidenció la escasez de recursos sanitarios y la desigualdad global. El desarrollo acelerado de vacunas fue un logro científico sin precedentes. La cooperación multilateral y la regulación sanitaria son esenciales.",
    "La corrupción institucional genera déficit de confianza y fracaso democrático. La transparencia, la educación cívica y la reforma judicial son herramientas de prevención. La innovación en auditoría digital reduce el fraude.",
    "El agotamiento profesional es una epidemia silenciosa en las organizaciones modernas. Las iniciativas de bienestar laboral y la regulación del trabajo remoto son respuestas emergentes. La prevención es más eficiente que la intervención tardía.",
    "La brecha tecnológica entre países desarrollados y en desarrollo profundiza la desigualdad. La educación digital, la inversión en infraestructura y la cooperación Sur-Sur son soluciones viables. El acceso renovable a internet es un derecho fundamental.",
    "La escasez hídrica provocada por la sequía amenaza la seguridad alimentaria global. El desarrollo de tecnologías de desalinización y la regulación del consumo son respuestas necesarias. La innovación agrícola reduce la vulnerabilidad ante el clima.",
    "La deuda soberana excesiva limita el desarrollo económico y genera crisis fiscales. La reforma tributaria, la reducción del déficit y la cooperación con organismos internacionales son soluciones estructurales. La educación financiera previene el sobreendeudamiento.",
    "La contaminación del aire y el agua genera epidemias y pérdidas en la productividad. La regulación ambiental estricta y la innovación en tecnologías limpias son respuestas efectivas. La cooperación regional reduce las emisiones transfronterizas.",
    "La extinción de especies y los incendios forestales son síntomas del colapso ecológico. La reforestación masiva y la regulación del monopolio energético son iniciativas urgentes. La adicción a los combustibles fósiles genera inundaciones y sequías.",
    "La quiebra de empresas genera desempleo y deuda social. El monopolio tecnológico es una amenaza para la innovación. La reforestación y la reducción de emisiones son soluciones para la extinción de ecosistemas.",
    # Nuevos textos para activar tokens sin cobertura
    "La acidificación de los océanos es una amenaza para los ecosistemas marinos. La conciencia ambiental y la sensibilización ciudadana son herramientas de prevención. La comunidad científica busca soluciones para el declive de la biodiversidad.",
    "La brecha de seguridad digital expone datos personales de millones de usuarios. La filtración de información es una crisis de privacidad. La coalición de empresas tecnológicas busca regulación para prevenir el fraude digital.",
    "La edición genética mediante CRISPR es un descubrimiento revolucionario. La modificación genética tiene limitaciones éticas y regulatorias. La comunidad médica debate los alcances de esta innovación biotecnológica.",
    "El declive industrial genera desempleo y pobreza en comunidades enteras. La reconversión laboral y la educación son soluciones para superar la obsolescencia económica. La coalición de sindicatos busca regulación para proteger a los trabajadores.",
    "La obsolescencia tecnológica es un cuello de botella para el desarrollo. La barrera de adopción digital limita el crecimiento de las economías emergentes. La sensibilización y la educación digital son herramientas de transformación.",
    "La batería de iones de litio es una innovación clave para la energía renovable. El almacenamiento energético supera la limitación de las fuentes intermitentes. La comunidad científica desarrolla soluciones para mejorar su eficiencia.",
    "La conciencia social sobre el cambio climático ha generado movimientos globales. La sensibilización ciudadana es el primer paso hacia la regulación ambiental. La coalición de naciones busca acuerdos para reducir emisiones.",
    "El declive de la democracia es una crisis institucional global. La brecha de confianza entre ciudadanos e instituciones genera fracaso político. La educación cívica y la transparencia son soluciones para superar esta limitación.",
]

WHITELIST_ESPANOL = [
    "bbc.com", "elpais.com", "expansion.com",
    "eleconomista.es", "reuters.com",
]

CORPUS_DINAMICO_PATH = Path("corpus_dinamico.json")
CORPUS_DINAMICO_MAX = 500   # máximo de textos guardados
CORPUS_DINAMICO_MIN_PALABRAS = 5   # mínimo de palabras nuevas para guardar un párrafo

def cargar_fuentes_corpus():
    """Carga URLs adicionales del corpus dinámico y las agrega a las listas de fuentes."""
    if not CORPUS_DINAMICO_PATH.exists():
        return
    try:
        with open(CORPUS_DINAMICO_PATH, encoding="utf-8") as f:
            corpus = json.load(f)
        fuentes_nuevas = corpus.get("fuentes", [])
        dominios_es = ["listindiario", "eldinero", "diariolibre", "cepal",
                       "portafolio", "gestion.pe", "infobae", "eleconomista.com.mx",
                       "bbc.com/mundo", "elpais", "expansion", "eleconomista.es",
                       "plato.stanford", "nature.com", "quantamagazine", "spectrum.ieee",
                       "imf.org", "worldbank", "bis.org"]
        agregadas = 0
        for url in fuentes_nuevas:
            es_espanol = any(d in url for d in dominios_es)
            if es_espanol:
                if url not in FUENTES_ESPANOL:
                    FUENTES_ESPANOL.append(url)
                    agregadas += 1
            else:
                if url not in FUENTES_SEMILLA:
                    FUENTES_SEMILLA.append(url)
                    agregadas += 1
        if agregadas:
            print(f"  [Corpus] {agregadas} fuentes nuevas cargadas del corpus dinamico")
    except Exception:
        pass

def cargar_corpus_dinamico():
    """Carga el corpus dinámico desde disco, combinado con el corpus estático."""
    textos = list(CORPUS_ESPANOL)  # siempre incluye el estático como base
    if CORPUS_DINAMICO_PATH.exists():
        try:
            with open(CORPUS_DINAMICO_PATH, encoding="utf-8") as f:
                dinamico = json.load(f)
            textos.extend(dinamico.get("textos", []))
        except Exception:
            pass
    return textos

def guardar_en_corpus(texto, memoria):
    """
    Evalúa si un texto tiene suficiente vocabulario nuevo para guardarlo.
    Si sí, lo agrega al corpus dinámico.
    """
    palabras = re.findall(r'[a-záéíóúüñ]{4,}', texto.lower())
    todos_tokens = set(k.split("_")[-1] for k in memoria.problemas) | \
                   set(k.split("_")[-1] for k in memoria.soluciones)

    palabras_utiles = set()
    for palabra in set(palabras):
        if palabra in MAPA_ES_TOKEN:
            if MAPA_ES_TOKEN[palabra] in todos_tokens:
                palabras_utiles.add(palabra)

    if len(palabras_utiles) < CORPUS_DINAMICO_MIN_PALABRAS:
        return False  # texto no tiene suficiente vocabulario

    # Cargar corpus actual
    if CORPUS_DINAMICO_PATH.exists():
        try:
            with open(CORPUS_DINAMICO_PATH, encoding="utf-8") as f:
                dinamico = json.load(f)
        except Exception:
            dinamico = {"textos": [], "total_guardados": 0}
    else:
        dinamico = {"textos": [], "total_guardados": 0}

    # Evitar duplicados aproximados (primeros 100 chars)
    firma = texto[:100]
    firmas = [t[:100] for t in dinamico["textos"]]
    if firma in firmas:
        return False

    # Agregar y mantener límite
    dinamico["textos"].append(texto[:1500])  # máx 1500 chars por texto
    dinamico["total_guardados"] = dinamico.get("total_guardados", 0) + 1

    # Si excede el máximo, eliminar los más viejos
    if len(dinamico["textos"]) > CORPUS_DINAMICO_MAX:
        dinamico["textos"] = dinamico["textos"][-CORPUS_DINAMICO_MAX:]

    with open(CORPUS_DINAMICO_PATH, "w", encoding="utf-8") as f:
        json.dump(dinamico, f, ensure_ascii=False, indent=2)

    return True

WHITELIST = [
    "hbr.org", "economist.com", "reuters.com", "weforum.org",
    "mckinsey.com", "techcrunch.com", "arxiv.org", "sciencedaily.com",
    "bloomberg.com", "wsj.com", "nature.com",
    "mit.edu", "stanford.edu", "harvard.edu",
    "bbc.com", "elpais.com", "expansion.com",
    "eleconomista.es",
]

# Palabras de TENSIÓN — señal de desequilibrio
PALABRAS_TENSION = {
    # Económicos
    "inflation", "recession", "unemployment", "debt", "deficit", "inequality",
    "poverty", "stagnation", "stagflation", "bankruptcy", "fraud", "corruption",
    # Climáticos
    "drought", "flood", "wildfire", "heatwave", "emissions", "deforestation",
    "extinction", "pollution", "contamination", "acidification",
    # Tecnológicos
    "cybersecurity", "outage", "vulnerability", "breach", "misinformation",
    "monopoly", "surveillance", "displacement", "obsolescence",
    # Sociales
    "burnout", "shortage", "scarcity", "underfunded", "overcrowded",
    "neglected", "discrimination", "displacement", "homelessness",
    # Salud
    "pandemic", "epidemic", "resistance", "overdose", "malnutrition",
    "obesity", "depression", "addiction", "mortality",
    # Genéricos pero útiles
    "crisis", "failure", "disruption", "collapse", "threat", "decline",
    "bottleneck", "limitation", "constraint", "barrier", "gap",
}

# Palabras de RESOLUCIÓN — señal de contrapeso
PALABRAS_RESOLUCION = {
    # Tecnológicas
    "algorithm", "automation", "artificial", "machine", "neural", "blockchain",
    "renewable", "battery", "solar", "hydrogen", "vaccine", "crispr", "gene",
    # Políticas
    "policy", "regulation", "legislation", "treaty", "reform", "subsidy",
    "incentive", "framework", "governance", "cooperation",
    # Científicas
    "discovered", "breakthrough", "developed", "invented", "synthesized",
    "engineered", "detected", "sequenced", "mapped", "modeled",
    # Empresariales
    "innovation", "startup", "scaled", "deployed", "launched", "implemented",
    "optimized", "streamlined", "transformed", "disrupted",
    # Sociales
    "education", "training", "awareness", "community", "coalition", "initiative",
    "program", "intervention", "prevention", "restoration",
}

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "this", "that", "these", "those", "it", "its",
    "as", "if", "than", "so", "up", "out", "about", "into", "through",
    "also", "not", "no", "can", "new", "one", "two", "all", "their", "they",
    "which", "who", "how", "what", "when", "where", "there", "here",
}

DELAY = 2.5
TECHO = 100.0
ENTREVISTA_CADA = 50
MAX_ENLACES = 20

HEADERS = {
    "User-Agent": "ANIMUS-Business-Research/1.0 (curiosity-driven; educational)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


# ──────────────────────────────────────────────────────────────────────────────
# 1. MEMORIA DUAL
# ──────────────────────────────────────────────────────────────────────────────

class MemoriaDual:
    def __init__(self):
        self.problemas = defaultdict(float)   # desequilibrios detectados
        self.soluciones = defaultdict(float)  # patrones de resolución
        self.conexiones = defaultdict(float)  # puentes problema-solución
        self.lenguaje = defaultdict(float)    # asociaciones español→token_interno
        self.paginas_visitadas = set()
        self.cargar()

    def cargar(self):
        if Path("memoria_business.json").exists():
            with open("memoria_business.json", "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    for k, v in data.get("problemas", {}).items():
                        self.problemas[k] = min(float(v), TECHO)
                    for k, v in data.get("soluciones", {}).items():
                        self.soluciones[k] = min(float(v), TECHO)
                    for k, v in data.get("conexiones", {}).items():
                        self.conexiones[k] = min(float(v), TECHO)
                    for k, v in data.get("lenguaje", {}).items():
                        self.lenguaje[k] = min(float(v), TECHO)
                    self.paginas_visitadas = set(data.get("paginas_visitadas", []))
                    print(f"📂 Memoria cargada: {len(self.problemas)} problemas, "
                          f"{len(self.soluciones)} soluciones, "
                          f"{len(self.conexiones)} conexiones, "
                          f"{len(self.lenguaje)} asociaciones de lenguaje.")
                except Exception as e:
                    print(f"⚠️  Memoria corrupta: {e}")
        else:
            print("🌱 Memoria nueva — comenzando desde cero.")

    def guardar(self):
        with open("memoria_business.json", "w", encoding="utf-8") as f:
            json.dump({
                "problemas": dict(self.problemas),
                "soluciones": dict(self.soluciones),
                "conexiones": dict(self.conexiones),
                "lenguaje": dict(self.lenguaje),
                "paginas_visitadas": list(self.paginas_visitadas),
                "ultima_actualizacion": datetime.now().isoformat(),
            }, f, indent=2, ensure_ascii=False)

    def reforzar_problema(self, clave, valor):
        self.problemas[clave] = min(self.problemas[clave] + valor, TECHO)

    def reforzar_solucion(self, clave, valor):
        self.soluciones[clave] = min(self.soluciones[clave] + valor, TECHO)

    def reforzar_conexion(self, prob, sol, valor):
        clave = f"{prob}__>{sol}"
        self.conexiones[clave] = min(self.conexiones[clave] + valor, TECHO)

    def top_conexiones(self, n=10):
        return sorted(self.conexiones.items(), key=lambda x: -x[1])[:n]

    def top_problemas(self, n=10):
        return sorted(self.problemas.items(), key=lambda x: -x[1])[:n]

    def top_soluciones(self, n=10):
        return sorted(self.soluciones.items(), key=lambda x: -x[1])[:n]

    def reforzar_lenguaje(self, palabra_es, token_interno, valor):
        """Asocia una palabra en español con un token interno conocido."""
        clave = f"{palabra_es}__={token_interno}"
        self.lenguaje[clave] = min(self.lenguaje[clave] + valor, TECHO)

    def top_lenguaje(self, n=20):
        return sorted(self.lenguaje.items(), key=lambda x: -x[1])[:n]

    def traducir(self, token_interno):
        """Encuentra la palabra en español más asociada a un token interno."""
        candidatos = {k: v for k, v in self.lenguaje.items()
                     if k.endswith(f"__={token_interno}")}
        if not candidatos:
            return token_interno  # si no sabe, devuelve el token crudo
        mejor = max(candidatos.items(), key=lambda x: x[1])
        return mejor[0].split("__=")[0]

    def articular_conexion(self, conexion_clave):
        """Intenta expresar una conexión en español."""
        partes = conexion_clave.split("__>")
        if len(partes) != 2:
            return conexion_clave
        token_prob = partes[0].split("_")[-1]
        token_sol = partes[1].split("_")[-1]
        palabra_prob = self.traducir(token_prob)
        palabra_sol = self.traducir(token_sol)
        return f"{palabra_prob} → {palabra_sol}"

    def escribir(self, pregunta_token):
        """
        Fase de ESCRITURA — genera una frase en español sobre un problema conocido.
        Busca el problema, encuentra sus mejores soluciones, construye una oración.
        """
        # Buscar el token en vocabulario de problemas
        palabra_es = self.traducir(pregunta_token)
        # Permitir palabras que son iguales en español e inglés (crisis, deficit, etc.)
        tiene_en_lenguaje = any(k.endswith(f"__={pregunta_token}") for k in self.lenguaje)
        if palabra_es == pregunta_token and not tiene_en_lenguaje:
            return None  # No conoce este problema en español

        # Encontrar las mejores conexiones para este problema
        conexiones_problema = {
            k: v for k, v in self.conexiones.items()
            if f"_{pregunta_token}__>" in k
        }
        # Añadir conexiones del libro que usan el mismo token
        for k, v in self.conexiones.items():
            partes = k.split("__>")
            if len(partes) == 2:
                token_izq = partes[0].split("_")[-1]
                if token_izq == pregunta_token:
                    conexiones_problema[k] = v
        if not conexiones_problema:
            return None

        # Ordenar por fuerza
        top_conexiones = sorted(conexiones_problema.items(), key=lambda x: -x[1])[:3]

        # Traducir soluciones
        soluciones_es = []
        for clave, fuerza in top_conexiones:
            token_sol = clave.split("__>")[1].split("_")[-1]
            palabra_sol = self.traducir(token_sol)
            if palabra_sol != token_sol:  # solo si tiene traducción
                soluciones_es.append(palabra_sol)

        if not soluciones_es:
            return None

        # Eliminar soluciones duplicadas
        soluciones_es = list(dict.fromkeys(soluciones_es))

        # Género del artículo — masculino
        MASCULINOS = {"fraude", "agotamiento", "colapso", "deficit", "déficit",
                      "desempleo", "monopolio", "riesgo", "fracaso", "sobreendeudamiento",
                      "problema", "conflicto", "acuerdo", "trato", "contrato",
                      "compromiso", "poder", "desacuerdo", "rechazo", "impasse"}
        articulo = "El" if palabra_es in MASCULINOS else "La"

        # Construir frase con plantillas
        if len(soluciones_es) == 1:
            frase = f"{articulo} {palabra_es} se resuelve con {soluciones_es[0]}."
        elif len(soluciones_es) == 2:
            frase = f"{articulo} {palabra_es} requiere {soluciones_es[0]} y {soluciones_es[1]}."
        else:
            frase = f"{articulo} {palabra_es} requiere {soluciones_es[0]}, {soluciones_es[1]} y {soluciones_es[2]}."

        return frase

    def responder(self, pregunta):
        """
        Fase de PRODUCCIÓN — responde una pregunta en español sobre desequilibrios.
        Analiza la pregunta, identifica el problema, genera respuesta articulada.
        """
        import re
        palabras = re.findall(r'[a-záéíóúüñ]{4,}', pregunta.lower())

        # Buscar qué problema menciona la pregunta
        respuestas = []
        for palabra in palabras:
            # Buscar en lenguaje — ¿conoce esta palabra?
            token = None
            for k in self.lenguaje:
                if k.startswith(f"{palabra}__="):
                    token = k.split("__=")[1]
                    break

            if token:
                frase = self.escribir(token)
                if frase:
                    respuestas.append(frase)

        if not respuestas:
            return "No tengo suficiente información sobre ese tema todavía."

        return " ".join(set(respuestas))


# ──────────────────────────────────────────────────────────────────────────────
# 2. PERCEPCIÓN Y ANÁLISIS DE DESEQUILIBRIO
# ──────────────────────────────────────────────────────────────────────────────

def extraer_dominio(url):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except:
        return ""

def dominio_permitido(url):
    dominio = extraer_dominio(url)
    return any(w in dominio for w in WHITELIST)

def extraer_palabras(texto, n=10):
    palabras = re.findall(r'\b[a-zA-Z]{4,}\b', texto.lower())
    freq = defaultdict(int)
    for p in palabras:
        if p not in STOPWORDS:
            freq[p] += 1
    return sorted(freq.items(), key=lambda x: -x[1])[:n]

def analizar_desequilibrio(texto):
    """
    Mide la tensión de una página.
    Alta tensión + baja resolución = desequilibrio puro = máxima novedad.
    """
    palabras = re.findall(r'\b[a-zA-Z]+\b', texto.lower())
    
    tension = sum(1 for p in palabras if p in PALABRAS_TENSION)
    resolucion = sum(1 for p in palabras if p in PALABRAS_RESOLUCION)
    
    total = len(palabras) or 1
    
    # Score de desequilibrio: alta tensión, baja resolución
    score_tension = tension / total * 100
    score_resolucion = resolucion / total * 100
    
    # Desequilibrio = tensión sin resolver
    desequilibrio = score_tension * (1 - min(score_resolucion / (score_tension + 0.001), 1))
    
    # Palabras de problema encontradas
    palabras_problema = [p for p in set(palabras) if p in PALABRAS_TENSION][:5]
    palabras_solucion = [p for p in set(palabras) if p in PALABRAS_RESOLUCION][:5]
    
    return {
        "desequilibrio": round(desequilibrio, 3),
        "tension": round(score_tension, 3),
        "resolucion": round(score_resolucion, 3),
        "palabras_problema": palabras_problema,
        "palabras_solucion": palabras_solucion,
    }

# Palabras de tensión en español
TENSION_ES = {
    "crisis", "fraude", "inflación", "desempleo", "deuda", "escasez",
    "contaminación", "desigualdad", "corrupción", "colapso", "amenaza",
    "riesgo", "pérdida", "fracaso", "brecha", "déficit", "pobreza",
    "sequía", "inundación", "pandemia", "recesión", "conflicto",
    "ciberseguridad", "agotamiento", "obstáculo", "limitación",
}

# Palabras de resolución en español
RESOLUCION_ES = {
    "innovación", "solución", "descubrimiento", "desarrollo", "política",
    "algoritmo", "automatización", "inteligencia", "artificial", "renovable",
    "vacuna", "educación", "reforma", "regulación", "iniciativa",
    "inversión", "tecnología", "cooperación", "programa", "estrategia",
    "reducción", "mejora", "transformación", "digitalización", "sostenible",
}

# Mapeo español → token interno conocido
# Incluye versiones con y sin acento para mayor cobertura
MAPA_ES_TOKEN = {
    # Problemas — con acento
    "fraude": "fraud", "crisis": "crisis", "inflación": "inflation",
    "desempleo": "unemployment", "deuda": "debt", "escasez": "shortage",
    "contaminación": "pollution", "desigualdad": "inequality",
    "corrupción": "corruption", "colapso": "collapse", "riesgo": "risk",
    "pérdida": "loss", "fracaso": "failure", "brecha": "gap",
    "déficit": "deficit", "pobreza": "poverty", "sequía": "drought",
    "pandemia": "pandemic", "recesión": "recession", "agotamiento": "burnout",
    "ciberseguridad": "cybersecurity", "limitación": "limitation",
    "amenaza": "threat", "quiebra": "bankruptcy", "adicción": "addiction",
    "epidemia": "epidemic", "inundación": "flood", "incendio": "wildfire",
    "emisiones": "emissions", "extinción": "extinction", "monopolio": "monopoly",
    # Problemas — sin acento (versiones alternativas)
    "inflacion": "inflation", "corrupcion": "corruption", "contaminacion": "pollution",
    "desigualdad": "inequality", "recesion": "recession", "limitacion": "limitation",
    "deficit": "deficit", "sequia": "drought", "pandemia": "pandemic",
    "perdida": "loss", "adiccion": "addiction", "inundacion": "flood",
    "extincion": "extinction", "emision": "emissions", "emision": "emissions",
    # Soluciones — con acento
    "innovación": "innovation", "solución": "solution",
    "descubrimiento": "discovered", "desarrollo": "developed",
    "política": "policy", "algoritmo": "algorithm",
    "automatización": "automation", "renovable": "renewable",
    "vacuna": "vaccine", "educación": "education",
    "reforma": "reform", "regulación": "regulation", "iniciativa": "initiative",
    "tecnología": "technology", "cooperación": "cooperation",
    "inversión": "incentive", "prevención": "prevention",
    "transformación": "transformed", "digitalización": "automation",
    # Soluciones — sin acento
    "innovacion": "innovation", "solucion": "solution",
    "politica": "policy", "automatizacion": "automation",
    "educacion": "education", "regulacion": "regulation",
    "tecnologia": "technology", "cooperacion": "cooperation",
    "inversion": "incentive", "prevencion": "prevention",
    "transformacion": "transformed",
    # Vocabulario de negociación
    "acuerdo": "solution", "trato": "solution", "solución": "solution", "solucion": "solution",
    "contrato": "regulation", "oferta": "initiative",
    "concesión": "reform", "concesion": "reform",
    "compromiso": "cooperation", "estrategia": "algorithm",
    "ventaja": "innovation", "negociación": "cooperation",
    "negociacion": "cooperation", "alianza": "cooperation",
    "coalición": "coalition", "coalicion": "coalition",
    "presión": "threat", "presion": "threat",
    "conflicto": "crisis", "desacuerdo": "gap",
    "rechazo": "failure", "pérdida": "loss", "perdida": "loss",
    "competencia": "gap", "poder": "incentive",
    # Palabras adicionales del corpus expandido
    "inundacion": "flood", "inundación": "flood",
    "quiebra": "bankruptcy", "quiebras": "bankruptcy",
    "pérdida": "loss", "perdida": "loss", "pérdidas": "loss",
    "colapso": "collapse", "fracaso": "failure",
    "amenaza": "threat", "amenazas": "threat",
    "algoritmo": "algorithm", "algoritmos": "algorithm",
    "descubrimiento": "discovered", "descubrimientos": "discovered",
    "iniciativa": "initiative", "iniciativas": "initiative",
    "contaminacion": "pollution", "contaminación": "pollution",
    "desempleo": "unemployment",
    "riesgo": "risk", "riesgos": "risk",
    "transformación": "transformed", "transformacion": "transformed",
    "limitacion": "limitation", "limitación": "limitation",
    "reforestacion": "restoration", "reforestación": "restoration",
    "sobreendeudamiento": "debt",
    "tecnologias": "technology", "tecnologías": "technology",
    "multilateral": "cooperation",

    # ── EXPANSIÓN v2 — vocabulario económico/empresarial ampliado ────────────
    # Más problemas
    "estancamiento": "stagnation", "estancacion": "stagnation",
    "endeudamiento": "debt", "deudas": "debt",
    "desaceleración": "recession", "desaceleracion": "recession",
    "volatilidad": "risk", "incertidumbre": "risk",
    "vulnerabilidad": "risk", "vulnerabilidades": "risk",
    "deterioro": "collapse", "declive": "collapse",
    "retroceso": "failure", "obstáculo": "failure", "obstaculo": "failure",
    "brecha": "gap", "brechas": "gap",
    "exclusión": "inequality", "exclusion": "inequality",
    "marginalización": "inequality", "marginalizacion": "inequality",
    "discriminación": "inequality", "discriminacion": "inequality",
    "impunidad": "corruption", "malversación": "corruption", "malversacion": "corruption",
    "evasión": "fraud", "evasion": "fraud", "evasión fiscal": "fraud",
    "especulación": "fraud", "especulacion": "fraud",
    "monopolización": "monopoly", "monopolizacion": "monopoly",
    "deforestación": "deforestation", "deforestacion": "deforestation",
    "sequía": "drought", "inundaciones": "flood",
    "huracán": "flood", "huracan": "flood", "tormenta": "flood",
    "terremoto": "collapse", "desastre": "collapse",
    "hambre": "poverty", "hambruna": "poverty",
    "analfabetismo": "poverty", "desnutrición": "poverty", "desnutricion": "poverty",
    "hacinamiento": "poverty", "precariedad": "poverty",
    "desplazamiento": "inequality", "migración": "inequality", "migracion": "inequality",
    "xenofobia": "inequality", "racismo": "inequality",
    "radicalismo": "collapse", "extremismo": "collapse", "terrorismo": "collapse",
    "desinformación": "misinformation", "desinformacion": "misinformation",
    "polarización": "crisis", "polarizacion": "crisis",
    "sobrecarga": "burnout", "estrés": "burnout", "estres": "burnout",
    "burnout": "burnout", "agotamiento": "burnout",
    "rezago": "gap", "atraso": "gap",
    "proteccionismo": "gap", "aranceles": "gap",
    "inflaciones": "inflation", "hiperinflación": "inflation", "hiperinflacion": "inflation",
    "deflación": "recession", "deflacion": "recession",
    "mora": "debt", "morosidad": "debt", "impago": "debt",
    # Más soluciones
    "modernización": "transformed", "modernizacion": "transformed",
    "digitalización": "automation", "digitalizacion": "automation",
    "inteligencia artificial": "algorithm", "inteligencia": "algorithm",
    "aprendizaje": "education", "capacitación": "education", "capacitacion": "education",
    "formación": "education", "formacion": "education",
    "investigación": "discovered", "investigacion": "discovered",
    "ciencia": "discovered", "científico": "discovered", "cientifico": "discovered",
    "innovaciones": "innovation", "emprendimiento": "innovation",
    "startup": "innovation", "startups": "innovation",
    "emprendedor": "innovation", "emprendedores": "innovation",
    "disrupción": "innovation", "disrupcion": "innovation",
    "sostenibilidad": "renewable", "sostenible": "renewable",
    "sustentabilidad": "renewable", "sustentable": "renewable",
    "energía": "renewable", "energia": "renewable",
    "solar": "renewable", "eólica": "renewable", "eolica": "renewable",
    "transición": "transformed", "transicion": "transformed",
    "descarbonización": "renewable", "descarbonizacion": "renewable",
    "reciclaje": "renewable", "reutilización": "renewable",
    "financiamiento": "incentive", "financiacion": "incentive", "financiación": "incentive",
    "subsidio": "incentive", "subsidios": "incentive",
    "crédito": "incentive", "credito": "incentive",
    "microcrédito": "incentive", "microcredito": "incentive",
    "presupuesto": "policy", "presupuestos": "policy",
    "gasto público": "policy", "gasto": "policy",
    "impuesto": "regulation", "impuestos": "regulation", "tributación": "regulation",
    "legislación": "regulation", "legislacion": "regulation",
    "normativa": "regulation", "normas": "regulation",
    "fiscalización": "regulation", "fiscalizacion": "regulation",
    "supervisión": "regulation", "supervision": "regulation",
    "transparencia": "regulation", "rendición": "regulation",
    "gobernanza": "regulation", "gobernabilidad": "regulation",
    "democracia": "reform", "democratización": "reform", "democratizacion": "reform",
    "participación": "reform", "participacion": "reform",
    "descentralización": "reform", "descentralizacion": "reform",
    "inclusión": "reform", "inclusion": "reform",
    "equidad": "reform", "igualdad": "reform",
    "diplomacia": "cooperation", "negociaciones": "cooperation",
    "tratado": "cooperation", "tratados": "cooperation",
    "acuerdos": "solution", "consenso": "cooperation",
    "solidaridad": "cooperation", "integración": "cooperation", "integracion": "cooperation",
    "globalización": "cooperation", "globalizacion": "cooperation",
    "digitalización": "automation", "automatización": "automation",
    "robótica": "automation", "robotica": "automation",
    "biotecnología": "discovered", "biotecnologia": "discovered",
    "nanotecnología": "discovered", "nanotecnologia": "discovered",
    "blockchain": "algorithm", "criptomoneda": "algorithm",
    "telemedicina": "prevention", "medicina": "prevention",
    "salud": "prevention", "sanidad": "prevention",
    "vacunación": "vaccine", "vacunacion": "vaccine",
    "tratamiento": "prevention", "terapia": "prevention",
    "infraestructura": "developed", "conectividad": "developed",
    "banda ancha": "developed", "internet": "developed",
    "vivienda": "developed", "urbanización": "developed", "urbanizacion": "developed",
    "saneamiento": "developed", "agua potable": "developed",
    "nutrición": "developed", "nutricion": "developed",
    "bienestar": "developed", "calidad de vida": "developed",
    "movilidad": "developed", "transporte": "developed",
    "logística": "developed", "logistica": "developed",
    "exportaciones": "developed", "exportación": "developed", "exportacion": "developed",
    "importaciones": "incentive", "comercio": "incentive",
    "productividad": "developed", "eficiencia": "developed",
    "competitividad": "developed", "crecimiento": "developed",
    # Sabiduría (Biblia)
    "sabiduría": "education", "sabiduria": "education",
    "humildad": "cooperation", "diligencia": "developed",
    "justicia": "reform", "justo": "reform",
    "verdad": "regulation", "consejo": "cooperation",
    "prudencia": "algorithm", "prudente": "algorithm",
    "conocimiento": "discovered", "entendimiento": "education",
    "honra": "incentive", "prosperidad": "developed",
    "integridad": "regulation", "rectitud": "reform",
    "necedad": "failure", "necio": "failure",
    "pereza": "poverty", "perezoso": "poverty",
    "orgullo": "failure", "soberbia": "failure",
    "codicia": "gap", "engaño": "fraud",
    "vanidad": "failure", "aflicción": "crisis",
    "angustia": "burnout", "misericordia": "prevention",
    # ── EXPANSIÓN v3 — 59 tokens sin palabra española ──────────────────────
    "neuronal": "neural", "red neuronal": "neural",
    "redes neuronales": "neural", "máquina": "machine", "maquina": "machine",
    "vigilancia": "surveillance", "monitoreo": "surveillance",
    "implementación": "implemented", "implementacion": "implemented",
    "optimización": "optimized", "optimizacion": "optimized",
    "programa": "program", "programas": "program",
    "entrenamiento": "training", "obesidad": "obesity",
    "depresión": "depression", "depresion": "depression",
    "malnutrición": "malnutrition", "malnutricion": "malnutrition",
    "sobredosis": "overdose", "resistencia": "resistance",
    "genes": "gene", "gen": "gene",
    "secuenciación": "sequenced", "secuenciacion": "sequenced",
    "intervención": "intervention", "intervencion": "intervention",
    "detección": "detected", "deteccion": "detected",
    "obsolescencia": "obsolescence",
    "hidrógeno": "hydrogen", "hidrogeno": "hydrogen",
    "solar": "solar", "fotovoltaico": "solar",
    "batería": "battery", "baterias": "battery",
    "desplazados": "displacement", "desplazamiento": "displacement",
    "personas sin hogar": "homelessness", "sin techo": "homelessness",
    "noticias falsas": "misinformation", "fake news": "misinformation",
    "conciencia": "awareness", "sensibilización": "awareness",
    "sensibilizacion": "awareness", "comunidad": "community",
    "comunidades": "community", "marco legal": "framework",
    "marco regulatorio": "framework", "marcos": "framework",
    "gobernanza": "governance",
    "incendios forestales": "wildfire",
    "ola de calor": "heatwave", "olas de calor": "heatwave",
    "acidificación": "acidification", "acidificacion": "acidification",
    "avance": "breakthrough", "avances": "breakthrough",
    "interrupción": "outage", "interrupcion": "outage",
    "apagón": "outage", "apagon": "outage",
    "declive": "decline", "declinación": "decline",
    "escalabilidad": "scaled", "escalado": "scaled",
    "lanzamiento": "launched", "lanzamientos": "launched",
    "invención": "invented", "invencion": "invented",
    "modelado": "modeled", "modelo": "modeled", "modelos": "modeled",
    "síntesis": "synthesized", "sintetizado": "synthesized",
    "mapeo": "mapped", "mapeado": "mapped",
    "simplificado": "streamlined", "coalición": "coalition",
    "coalicion": "coalition",
    "ia generativa": "artificial",
    "autoconciencia": "awareness",
    "brecha de datos": "breach",
    "edición genómica": "crispr",
    "edicion genomica": "crispr",
    "modificación genética": "crispr",
    "oligopolio": "monopoly",
    "austeridad": "austerity",
    "arancel": "tariff",
    "sanción": "sanction",
    "sancion": "sanction",
    "embargo": "sanction",
    "deserción": "dropout",
    "desercion": "dropout",
    "abandono escolar": "dropout",
    "brecha digital": "digital_divide",
    "exclusión digital": "digital_divide",
    "privacidad": "privacy",
    "vigilancia masiva": "surveillance",
    "adicción tecnológica": "tech_addiction",
    "adiccion tecnologica": "tech_addiction",
    "fragmentación social": "polarization",
    "agotamiento laboral": "burnout",
    "quemado": "burnout",
    "estrés crónico": "burnout",
    "barrera": "barrier",
    # ── Últimos 15 tokens sin cubrir ───────────────────────────────────────
    "artificial": "artificial", "inteligencia artificial": "artificial",
    "ia": "artificial", "cadena de bloques": "blockchain",
    "criptomoneda": "blockchain", "criptomonedas": "blockchain",
    "cuello de botella": "bottleneck", "cuellos de botella": "bottleneck",
    "brecha de seguridad": "breach", "filtración": "breach",
    "filtración de datos": "breach", "filtracion": "breach",
    "contaminación": "contamination", "contaminacion": "contamination",
    "edición genética": "crispr", "crispr": "crispr",
    "despliegue": "deployed", "desplegado": "deployed",
    "discriminación racial": "discrimination",
    "perturbado": "disrupted", "interrumpido": "disrupted",
    "perturbación": "disruption", "perturbacion": "disruption",
    "diseñado genéticamente": "engineered", "modificado genéticamente": "engineered",
    "ley": "legislation", "leyes": "legislation",
    "empresa emergente": "startup", "empresa nueva": "startup",
    "subvención": "subsidy", "subvenciones": "subsidy",
    "vulnerabilidad": "vulnerability", "vulnerabilidades": "vulnerability",
}

def procesar_espanol(texto, memoria):
    """
    Lee texto en español y refuerza asociaciones palabra→token_interno.
    Esta es la fase de ENTENDER — el agente mapea español a sus tokens conocidos.
    """
    # Regex compatible con Unicode — detecta palabras con acentos correctamente
    palabras = re.findall(r'[a-záéíóúüñ]{4,}', texto.lower())
    asociaciones_nuevas = 0

    # Buscar conocimiento previo en TODOS los dominios
    todos_problemas = set(k.split("_")[-1] for k in memoria.problemas)
    todos_soluciones = set(k.split("_")[-1] for k in memoria.soluciones)

    for palabra in set(palabras):
        if palabra in MAPA_ES_TOKEN:
            token = MAPA_ES_TOKEN[palabra]
            en_problemas = token in todos_problemas
            en_soluciones = token in todos_soluciones

            if en_problemas or en_soluciones:
                conocimiento_total = sum(
                    v for k, v in memoria.problemas.items() if k.endswith(f"_{token}")
                ) + sum(
                    v for k, v in memoria.soluciones.items() if k.endswith(f"_{token}")
                )
                fuerza = min(conocimiento_total / 20.0, 3.0)  # más fuerza por exposición
                memoria.reforzar_lenguaje(palabra, token, fuerza)
                asociaciones_nuevas += 1

    return asociaciones_nuevas


def _playwright_disponible():
    try:
        import playwright
        return True
    except ImportError:
        return False


def _cargar_con_playwright(url, timeout=15):
    """D06: Load dynamic JS pages using Playwright headless browser."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": HEADERS["User-Agent"]})
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            html = page.content()
            browser.close()
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        texto = soup.get_text(separator=" ", strip=True)
        texto = re.sub(r'\s+', ' ', texto)[:8000]
        titulo = soup.title.string if soup.title else url
        enlaces = []
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            if dominio_permitido(href) and href.startswith("http"):
                enlaces.append(href)
        return {
            "url": url, "titulo": (titulo or url)[:100],
            "texto": texto, "enlaces": list(set(enlaces))[:MAX_ENLACES],
            "dominio": extraer_dominio(url), "modo": "playwright",
        }
    except Exception:
        return None


def _es_pagina_dinamica(html_texto):
    if not html_texto or len(html_texto.strip()) < 300:
        return True
    senales = ["You need to enable JavaScript", "Please enable JavaScript",
               "__NEXT_DATA__", "id=\"__nuxt\"", "<noscript>"]
    return any(s in html_texto for s in senales)


def cargar_pagina(url, timeout=10):
    """D06: Load page with automatic Playwright fallback for dynamic content."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        html_raw = resp.text
        soup = BeautifulSoup(html_raw, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        texto = soup.get_text(separator=" ", strip=True)
        texto = re.sub(r'\s+', ' ', texto)[:8000]
        if _es_pagina_dinamica(html_raw) or len(texto.strip()) < 200:
            if _playwright_disponible():
                pw = _cargar_con_playwright(url, timeout)
                if pw and len(pw["texto"]) > len(texto):
                    return pw
        titulo = soup.title.string if soup.title else url
        enlaces = []
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            if dominio_permitido(href) and href.startswith("http"):
                enlaces.append(href)
        return {
            "url": url, "titulo": (titulo or url)[:100],
            "texto": texto, "enlaces": list(set(enlaces))[:MAX_ENLACES],
            "dominio": extraer_dominio(url), "modo": "requests",
        }
    except Exception:
        if _playwright_disponible():
            return _cargar_con_playwright(url, timeout)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# 3. VOLUNTAD
# ──────────────────────────────────────────────────────────────────────────────

class Voluntad:
    def __init__(self, memoria):
        self.memoria = memoria
        self.ultimo_dominio = None
        self.contador_dominio = 0
        self.modo = "explorar"  # explorar | profundizar

    def elegir_siguiente(self, enlaces, url_actual):
        if not enlaces:
            return random.choice(FUENTES_SEMILLA)

        # Forzar cambio de dominio si lleva mucho tiempo en el mismo
        if self.contador_dominio > 12:
            dominio_actual = extraer_dominio(url_actual)
            otras = [s for s in FUENTES_SEMILLA if dominio_actual not in s]
            print(f"  🌱 Saltando dominio tras {self.contador_dominio} páginas")
            self.contador_dominio = 0
            return random.choice(otras)

        # Puntuar cada enlace
        pesos = []
        for url in enlaces:
            peso = self._puntuar_enlace(url)
            pesos.append(max(peso, 0.1))

        elegido = random.choices(enlaces, weights=pesos)[0]

        dominio = extraer_dominio(elegido)
        if dominio == self.ultimo_dominio:
            self.contador_dominio += 1
        else:
            self.contador_dominio = 0
            self.ultimo_dominio = dominio

        return elegido

    def _puntuar_enlace(self, url):
        """Estima el valor de un enlace por su potencial de desequilibrio."""
        palabras_url = re.findall(r'\b[a-zA-Z]{4,}\b', url.lower())
        
        score = 1.0
        
        # Bonus si el URL sugiere problema
        for p in palabras_url:
            if p in PALABRAS_TENSION:
                score += 3.0
            elif p in PALABRAS_RESOLUCION:
                score += 1.5
        
        # Bonus por dominio de alta calidad
        dominio = extraer_dominio(url)
        if any(d in dominio for d in ["hbr.org", "economist.com", "weforum.org", "mckinsey.com"]):
            score += 2.0
        elif any(d in dominio for d in ["arxiv.org", "nature.com", "mit.edu"]):
            score += 1.5

        # Penalizar si ya visitamos esta URL
        if url in self.memoria.paginas_visitadas:
            score *= 0.1

        return score


# ──────────────────────────────────────────────────────────────────────────────
# 4. ENTREVISTADOR
# ──────────────────────────────────────────────────────────────────────────────

class Entrevistador:
    def __init__(self):
        self.entrevistas = []
        self._cargar()

    def _cargar(self):
        if Path("entrevistas_business.json").exists():
            with open("entrevistas_business.json", "r", encoding="utf-8") as f:
                try:
                    self.entrevistas = json.load(f)
                except:
                    self.entrevistas = []

    def entrevistar(self, pagina_num, memoria, url_actual, titulo):
        top_problemas = memoria.top_problemas(5)
        top_soluciones = memoria.top_soluciones(5)
        top_conexiones = memoria.top_conexiones(5)

        obs = {
            "pagina": pagina_num,
            "timestamp": datetime.now().isoformat(),
            "url_actual": url_actual,
            "titulo": titulo,
            "total_problemas": len(memoria.problemas),
            "total_soluciones": len(memoria.soluciones),
            "total_conexiones": len(memoria.conexiones),
            "top_problemas": [(k, round(v, 1)) for k, v in top_problemas],
            "top_soluciones": [(k, round(v, 1)) for k, v in top_soluciones],
            "top_conexiones": [(k, round(v, 1)) for k, v in top_conexiones],
        }

        self.entrevistas.append(obs)

        with open("entrevistas_business.json", "w", encoding="utf-8") as f:
            json.dump(self.entrevistas, f, indent=2, ensure_ascii=False)

        print("\n" + "="*65)
        print(f"  ENTREVISTA — Página {pagina_num}")
        print(f"  Ahora en: {titulo[:55]}")
        print(f"  Problemas detectados: {len(memoria.problemas)} | "
              f"Soluciones: {len(memoria.soluciones)} | "
              f"Conexiones: {len(memoria.conexiones)}")
        print()
        print("  Desequilibrios más frecuentes:")
        for k, v in top_problemas[:3]:
            print(f"    ⚡ {k}: {v:.1f}")
        print()
        print("  Patrones de resolución:")
        for k, v in top_soluciones[:3]:
            print(f"    ✅ {k}: {v:.1f}")
        print()
        print("  Conexiones emergentes (problema → solución):")
        for k, v in top_conexiones[:3]:
            partes = k.split("__>")
            if len(partes) == 2:
                en_espanol = memoria.articular_conexion(k)
                print(f"    🔗 {partes[0].split('_')[-1]} → {partes[1].split('_')[-1]}: {v:.1f}")
                if en_espanol != k:
                    print(f"       💬 En español: {en_espanol}")
        print()
        print(f"  Vocabulario en español: {len(memoria.lenguaje)} asociaciones")
        top_vocab = memoria.top_lenguaje(5)
        for k, v in top_vocab:
            partes = k.split("__=")
            if len(partes) == 2:
                print(f"    📖 '{partes[0]}' = {partes[1]}: {v:.2f}")
        print("="*65 + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# 5. AGENTE PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────

class AnimusBusiness:
    def __init__(self):
        cargar_fuentes_corpus()  # Carga URLs del corpus dinamico antes de empezar
        self.memoria = MemoriaDual()
        self.voluntad = Voluntad(self.memoria)
        self.entrevistador = Entrevistador()
        self.paginas_sesion = 0
        self.url_actual = random.choice(FUENTES_SEMILLA)

    def procesar_pagina(self, pagina):
        texto = pagina["texto"]
        dominio = pagina["dominio"]
        url = pagina["url"]

        # Analizar desequilibrio
        analisis = analizar_desequilibrio(texto)
        desequilibrio = analisis["desequilibrio"]
        palabras_clave = extraer_palabras(texto, n=8)
        palabras_top = [p for p, _ in palabras_clave]

        # Reforzar memoria de problemas si hay tensión alta
        if analisis["tension"] > 0.3:
            for palabra in analisis["palabras_problema"]:
                clave = f"{dominio}_{palabra}"
                self.memoria.reforzar_problema(clave, analisis["tension"] * 2)

        # Reforzar memoria de soluciones si hay resolución
        if analisis["resolucion"] > 0.1:
            for palabra in analisis["palabras_solucion"]:
                clave = f"{dominio}_{palabra}"
                self.memoria.reforzar_solucion(clave, analisis["resolucion"] * 2)

        # Detectar conexiones: páginas que tienen AMBOS problema Y solución
        if analisis["palabras_problema"] and analisis["palabras_solucion"]:
            for prob in analisis["palabras_problema"][:2]:
                for sol in analisis["palabras_solucion"][:2]:
                    prob_clave = f"{dominio}_{prob}"
                    sol_clave = f"{dominio}_{sol}"
                    fuerza = desequilibrio * 0.5
                    self.memoria.reforzar_conexion(prob_clave, sol_clave, fuerza)

        # Marcar visitada
        self.memoria.paginas_visitadas.add(url)

        return analisis, palabras_top

    def correr(self, max_paginas=500):
        print(f"\n⚡ ANIMUS Business | {datetime.now().strftime('%H:%M:%S')}")
        print(f"   Detectando desequilibrios. Aprendiendo a nombrarlos.")
        print(f"   Iniciando en: {self.url_actual}\n")

        pagina_num = len(self.memoria.paginas_visitadas)
        # Cada 3 páginas en inglés, 1 en español
        turno_espanol = 0

        for i in range(max_paginas):
            pagina_num += 1
            self.paginas_sesion += 1

            # Turno en español cada 3 páginas
            modo_espanol = (turno_espanol >= 2)
            if modo_espanol:
                self.url_actual = random.choice(FUENTES_ESPANOL)
                turno_espanol = 0
            else:
                turno_espanol += 1

            print(f"  Página {pagina_num:>4} {'🇪🇸' if modo_espanol else '🌐'} | {self.url_actual[:62]}")

            pagina = cargar_pagina(self.url_actual)

            if pagina is None:
                print(f"  ⚠️  Error — saltando a semilla")
                self.url_actual = random.choice(FUENTES_SEMILLA)
                time.sleep(DELAY)
                continue

            # Si es página en español, procesar para aprendizaje de lenguaje
            if modo_espanol:
                nuevas = procesar_espanol(pagina["texto"], self.memoria)
                # Guardar página si tiene vocabulario útil
                if pagina["texto"] and len(pagina["texto"]) > 200:
                    guardado = guardar_en_corpus(pagina["texto"], self.memoria)
                    if guardado:
                        print(f"         💾 Párrafo guardado en corpus dinámico")
                # Reforzar con corpus dinámico — incluye textos acumulados
                corpus_actual = cargar_corpus_dinamico()
                for _ in range(3):
                    texto_corpus = random.choice(corpus_actual)
                    nuevas_corpus = procesar_espanol(texto_corpus, self.memoria)
                    nuevas += nuevas_corpus
                print(f"         🗣️  Procesadas: {nuevas} | "
                      f"Vocabulario: {len(self.memoria.lenguaje)} | "
                      f"Corpus: {len(corpus_actual)}")
                self.memoria.paginas_visitadas.add(pagina["url"])
                if pagina_num % 10 == 0:
                    self.memoria.guardar()
                self.url_actual = random.choice(FUENTES_ESPANOL)
                time.sleep(DELAY + random.uniform(0, 1.0))
                continue

            analisis, palabras_top = self.procesar_pagina(pagina)

            # Indicador visual de desequilibrio
            nivel = "⚡⚡⚡" if analisis["desequilibrio"] > 1.0 else \
                    "⚡⚡" if analisis["desequilibrio"] > 0.5 else \
                    "⚡" if analisis["desequilibrio"] > 0.2 else "·"

            print(f"         {nivel} Deseq: {analisis['desequilibrio']:.3f} | "
                  f"Tensión: {analisis['tension']:.3f} | "
                  f"Resolución: {analisis['resolucion']:.3f}")

            if analisis["palabras_problema"]:
                print(f"         Problemas: {', '.join(analisis['palabras_problema'][:3])}")
            if analisis["palabras_solucion"]:
                print(f"         Soluciones: {', '.join(analisis['palabras_solucion'][:3])}")

            # Entrevista periódica
            if pagina_num % ENTREVISTA_CADA == 0:
                self.entrevistador.entrevistar(
                    pagina_num, self.memoria,
                    self.url_actual, pagina["titulo"]
                )

            # Siguiente enlace
            self.url_actual = self.voluntad.elegir_siguiente(
                pagina["enlaces"], self.url_actual
            )

            # Guardar periódicamente
            if pagina_num % 10 == 0:
                self.memoria.guardar()

            time.sleep(DELAY + random.uniform(0, 1.0))

        self.memoria.guardar()

        print(f"\n✅ Sesión terminada.")
        print(f"   Páginas esta sesión: {self.paginas_sesion}")
        print(f"   Total visitadas: {len(self.memoria.paginas_visitadas)}")
        print(f"   Problemas detectados: {len(self.memoria.problemas)}")
        print(f"   Soluciones encontradas: {len(self.memoria.soluciones)}")
        print(f"   Conexiones emergentes: {len(self.memoria.conexiones)}")

        # Reporte final
        print(f"\n{'='*65}")
        print(f"  REPORTE FINAL — Conexiones articuladas en español:")
        for k, v in self.memoria.top_conexiones(10):
            partes = k.split("__>")
            if len(partes) == 2:
                token_prob = partes[0].split("_")[-1]
                token_sol = partes[1].split("_")[-1]
                es = self.memoria.articular_conexion(k)
                print(f"  🔗 {token_prob} → {token_sol}: {v:.1f}")
                if es != k:
                    print(f"     💬 '{es}'")
        print()
        print(f"  Vocabulario español adquirido: {len(self.memoria.lenguaje)} palabras")
        print(f"{'='*65}")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "preguntar":
        # Modo interactivo — el agente responde preguntas
        agente = AnimusBusiness()
        print(f"\n🤖 ANIMUS Business — Modo Interactivo")
        print(f"   Vocabulario: {len(agente.memoria.lenguaje)} palabras")
        print(f"   Conexiones: {len(agente.memoria.conexiones)}")
        print(f"   Escribe tu pregunta o 'salir' para terminar.\n")
        while True:
            pregunta = input("❓ Pregunta: ").strip()
            if pregunta.lower() in ["salir", "exit", "quit"]:
                break
            if not pregunta:
                continue
            respuesta = agente.memoria.responder(pregunta)
            print(f"💬 {respuesta}\n")
    else:
        max_paginas = int(sys.argv[1]) if len(sys.argv) > 1 else 500
        agente = AnimusBusiness()
        agente.correr(max_paginas)

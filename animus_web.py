"""
ANIMUS Web — Agente explorador de la web por curiosidad pura
Sin objetivos externos. Sin supervisión. Solo novedad.
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
from bs4 import BeautifulSoup

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────────────────────────────────────

WHITELIST = [
    "reuters.com",
    "nature.com",
    "arxiv.org",
    "bbc.com",
    "wikipedia.org",
    "sciencedaily.com",
    "economist.com",
    "nationalgeographic.com",
    "pubmed.ncbi.nlm.nih.gov",
    "imf.org",
]

SEMILLAS = [
    "https://www.reuters.com",
    "https://www.nature.com/news",
    "https://arxiv.org/list/cs.AI/recent",
    "https://www.bbc.com/news",
    "https://en.wikipedia.org/wiki/Special:Random",
    "https://www.sciencedaily.com",
    "https://www.economist.com",
    "https://www.nationalgeographic.com/science",
]

DELAY_ENTRE_REQUESTS = 2.5  # segundos — respetuoso con los servidores
MAX_ENLACES_POR_PAGINA = 20  # evaluar solo los primeros N enlaces
TECHO_CRITERIO = 100.0
ENTREVISTA_CADA = 50  # páginas

# Stopwords para extracción de palabras clave
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "this", "that", "these", "those", "it", "its",
    "as", "if", "than", "so", "up", "out", "about", "into", "through",
    "during", "before", "after", "over", "under", "between", "each", "more",
    "also", "not", "no", "can", "new", "one", "two", "all", "their", "they",
    "which", "who", "how", "what", "when", "where", "there", "here", "been",
    "de", "la", "el", "en", "los", "las", "un", "una", "del", "por", "que",
}

HEADERS = {
    "User-Agent": "ANIMUS-Web-Research-Agent/1.0 (curiosity-driven; educational)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


# ──────────────────────────────────────────────────────────────────────────────
# 1. MEMORIA
# ──────────────────────────────────────────────────────────────────────────────

class Memoria:
    def __init__(self, path="memoria_web.json"):
        self.path = path
        self.criterios = defaultdict(float)
        self.paginas_visitadas = set()
        self.cargar()

    def cargar(self):
        if Path(self.path).exists():
            with open(self.path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    for k, v in data.get("criterios", {}).items():
                        self.criterios[k] = min(float(v), TECHO_CRITERIO)
                    self.paginas_visitadas = set(data.get("paginas_visitadas", []))
                    print(f"📂 Memoria cargada: {len(self.criterios)} criterios, "
                          f"{len(self.paginas_visitadas)} páginas visitadas.")
                except Exception as e:
                    print(f"⚠️  Memoria corrupta: {e}")
        else:
            print("🌱 Memoria nueva — comenzando desde cero.")

    def guardar(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({
                "criterios": dict(self.criterios),
                "paginas_visitadas": list(self.paginas_visitadas),
                "ultima_actualizacion": datetime.now().isoformat(),
            }, f, indent=2, ensure_ascii=False)

    def reforzar(self, clave, valor):
        self.criterios[clave] = min(
            self.criterios[clave] + valor,
            TECHO_CRITERIO
        )

    def conoce(self, clave):
        return self.criterios.get(clave, 0.0)


# ──────────────────────────────────────────────────────────────────────────────
# 2. PERCEPCIÓN
# ──────────────────────────────────────────────────────────────────────────────

def extraer_dominio(url):
    """Extrae el dominio base de una URL."""
    try:
        parsed = urlparse(url)
        dominio = parsed.netloc.replace("www.", "")
        return dominio
    except:
        return ""

def dominio_en_whitelist(url):
    """Verifica si la URL pertenece a una fuente fidedigna."""
    dominio = extraer_dominio(url)
    return any(w in dominio for w in WHITELIST)

def extraer_palabras_clave(texto, n=5):
    """Extrae las N palabras más frecuentes del texto, ignorando stopwords."""
    palabras = re.findall(r'\b[a-zA-Z]{4,}\b', texto.lower())
    frecuencia = defaultdict(int)
    for p in palabras:
        if p not in STOPWORDS:
            frecuencia[p] += 1
    top = sorted(frecuencia.items(), key=lambda x: -x[1])[:n]
    return [p for p, _ in top]

def construir_clave(dominio, palabras_clave):
    """Construye la clave de criterio: dominio_palabra1_palabra2..."""
    palabras_limpias = [p[:20] for p in palabras_clave[:3]]
    return dominio + "_" + "_".join(palabras_limpias)

def cargar_pagina(url, timeout=10):
    """Carga una página web y retorna su contenido parseado."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extraer texto limpio
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        texto = soup.get_text(separator=" ", strip=True)
        texto = re.sub(r'\s+', ' ', texto)[:5000]  # primeras 5000 chars

        # Extraer título
        titulo = soup.title.string if soup.title else url

        # Extraer enlaces válidos
        enlaces = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            href_completo = urljoin(url, href)
            if dominio_en_whitelist(href_completo) and href_completo.startswith("http"):
                enlaces.append(href_completo)

        return {
            "url": url,
            "titulo": titulo[:100] if titulo else url,
            "texto": texto,
            "enlaces": list(set(enlaces))[:MAX_ENLACES_POR_PAGINA],
            "dominio": extraer_dominio(url),
        }
    except Exception as e:
        return None


# ──────────────────────────────────────────────────────────────────────────────
# 3. NOVEDAD
# ──────────────────────────────────────────────────────────────────────────────

def calcular_novedad(dominio, palabras_clave, memoria):
    """
    Cuántas de estas palabras clave son nuevas para el agente.
    Más palabras nuevas = más novedad = más valor.
    """
    novedad = 0.0
    for palabra in palabras_clave:
        clave = f"{dominio}_{palabra}"
        conocimiento_previo = memoria.conoce(clave)
        if conocimiento_previo < 10.0:
            novedad += (10.0 - conocimiento_previo) / 10.0
    return novedad

def estimar_novedad_enlace(url, memoria):
    """
    Estima la novedad de un enlace sin cargarlo,
    basándose en el dominio y palabras del URL.
    """
    dominio = extraer_dominio(url)
    palabras_url = re.findall(r'\b[a-zA-Z]{4,}\b', url.lower())
    palabras_url = [p for p in palabras_url if p not in STOPWORDS][:5]

    novedad = 0.0
    # Novedad por dominio poco visitado
    clave_dominio = f"dominio_{dominio}"
    visitas_dominio = memoria.conoce(clave_dominio)
    novedad += max(0, 5.0 - visitas_dominio * 0.5)

    # Novedad por palabras del URL
    for p in palabras_url:
        clave = f"{dominio}_{p}"
        if memoria.conoce(clave) < 5.0:
            novedad += 1.0

    return novedad


# ──────────────────────────────────────────────────────────────────────────────
# 4. VOLUNTAD
# ──────────────────────────────────────────────────────────────────────────────

class Voluntad:
    def __init__(self, memoria):
        self.memoria = memoria
        self.ultimo_dominio = None
        self.contador_dominio = 0

    def elegir_siguiente(self, enlaces, pagina_actual_url):
        """Elige el próximo enlace por novedad probabilística."""
        if not enlaces:
            return random.choice(SEMILLAS)

        # Forzar salto a semilla diferente si lleva >15 páginas en mismo dominio
        if self.contador_dominio > 15:
            dominio_actual = extraer_dominio(pagina_actual_url)
            semillas_otras = [s for s in SEMILLAS if dominio_actual not in s]
            print(f"  🌱 Saltando a nueva fuente tras {self.contador_dominio} páginas en {dominio_actual}")
            self.contador_dominio = 0
            return random.choice(semillas_otras)

        # Anti-obsesión: si lleva muchos pasos en el mismo dominio, penalizar
        pesos = []
        for url in enlaces:
            novedad = estimar_novedad_enlace(url, self.memoria)
            dominio = extraer_dominio(url)

            # Penalizar si es el mismo dominio de siempre
            if dominio == self.ultimo_dominio and self.contador_dominio > 10:
                novedad *= 0.3

            pesos.append(max(novedad, 0.1))  # mínimo 0.1 para exploración

        elegido = random.choices(enlaces, weights=pesos)[0]

        # Actualizar contador de dominio
        dominio_elegido = extraer_dominio(elegido)
        if dominio_elegido == self.ultimo_dominio:
            self.contador_dominio += 1
        else:
            self.contador_dominio = 0
            self.ultimo_dominio = dominio_elegido

        return elegido


# ──────────────────────────────────────────────────────────────────────────────
# 5. ENTREVISTADOR
# ──────────────────────────────────────────────────────────────────────────────

class Entrevistador:
    def __init__(self, path="entrevistas_web.json"):
        self.path = path
        self.entrevistas = []
        self._cargar()

    def _cargar(self):
        if Path(self.path).exists():
            with open(self.path, "r", encoding="utf-8") as f:
                try:
                    self.entrevistas = json.load(f)
                except:
                    self.entrevistas = []

    def entrevistar(self, pagina_num, memoria, url_actual, titulo_actual):
        criterios = memoria.criterios

        # Top 10 criterios más valorados
        top = sorted(criterios.items(), key=lambda x: -x[1])[:10]

        # Dominios más visitados
        dominios = defaultdict(float)
        for k, v in criterios.items():
            partes = k.split("_")
            if len(partes) >= 2:
                dominios[partes[0]] += v
        top_dominios = sorted(dominios.items(), key=lambda x: -x[1])[:5]

        # Palabras clave más valoradas (excluyendo dominios)
        palabras = defaultdict(float)
        for k, v in criterios.items():
            partes = k.split("_")
            for p in partes[1:]:
                if len(p) > 3:
                    palabras[p] += v
        top_palabras = sorted(palabras.items(), key=lambda x: -x[1])[:10]

        obs = {
            "pagina": pagina_num,
            "timestamp": datetime.now().isoformat(),
            "url_actual": url_actual,
            "titulo_actual": titulo_actual,
            "total_criterios": len(criterios),
            "paginas_visitadas": len(memoria.paginas_visitadas),
            "top_criterios": [(k, round(v, 1)) for k, v in top],
            "top_dominios": [(d, round(v, 1)) for d, v in top_dominios],
            "top_palabras": [(p, round(v, 1)) for p, v in top_palabras],
        }

        self.entrevistas.append(obs)

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.entrevistas, f, indent=2, ensure_ascii=False)

        print("\n" + "="*60)
        print(f"  ENTREVISTA — Página {pagina_num}")
        print(f"  Ahora en: {titulo_actual[:50]}")
        print(f"  Criterios acumulados: {len(criterios)}")
        print(f"  Dominios que más valoro:")
        for d, v in top_dominios:
            print(f"    {d}: {v:.1f}")
        print(f"  Conceptos que más me atraen:")
        for p, v in top_palabras[:5]:
            print(f"    {p}: {v:.1f}")
        print("="*60 + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# 6. AGENTE PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────

class AnimusWeb:
    def __init__(self):
        self.memoria = Memoria()
        self.voluntad = Voluntad(self.memoria)
        self.entrevistador = Entrevistador()
        self.paginas_esta_sesion = 0
        self.url_actual = random.choice(SEMILLAS)

    def procesar_pagina(self, pagina):
        """Procesa una página y actualiza los criterios."""
        dominio = pagina["dominio"]
        texto = pagina["texto"]
        url = pagina["url"]

        # Extraer palabras clave
        palabras_clave = extraer_palabras_clave(texto, n=7)

        # Calcular novedad real
        novedad = calcular_novedad(dominio, palabras_clave, self.memoria)

        # Reforzar criterios
        clave_principal = construir_clave(dominio, palabras_clave)
        self.memoria.reforzar(clave_principal, novedad)

        # Reforzar también por palabra individual
        for palabra in palabras_clave:
            clave_palabra = f"{dominio}_{palabra}"
            self.memoria.reforzar(clave_palabra, novedad / len(palabras_clave))

        # Registrar visita al dominio
        self.memoria.reforzar(f"dominio_{dominio}", 1.0)

        # Marcar página como visitada
        self.memoria.paginas_visitadas.add(url)

        return novedad, palabras_clave

    def correr(self, max_paginas=500):
        print(f"\n🌐 ANIMUS Web | {datetime.now().strftime('%H:%M:%S')}")
        print(f"   Curiosidad pura. Sin objetivos. Solo novedad.")
        print(f"   Iniciando en: {self.url_actual}\n")

        pagina_num = len(self.memoria.paginas_visitadas)

        for i in range(max_paginas):
            pagina_num += 1
            self.paginas_esta_sesion += 1

            print(f"  Página {pagina_num:>4} | {self.url_actual[:70]}")

            # Cargar página
            pagina = cargar_pagina(self.url_actual)

            if pagina is None:
                print(f"  ⚠️  Error cargando — saltando a semilla")
                self.url_actual = random.choice(SEMILLAS)
                time.sleep(DELAY_ENTRE_REQUESTS)
                continue

            # Procesar y actualizar memoria
            novedad, palabras_clave = self.procesar_pagina(pagina)

            print(f"         Novedad: {novedad:.2f} | "
                  f"Conceptos: {', '.join(palabras_clave[:4])} | "
                  f"Criterios: {len(self.memoria.criterios)}")

            # Entrevista periódica
            if pagina_num % ENTREVISTA_CADA == 0:
                self.entrevistador.entrevistar(
                    pagina_num, self.memoria,
                    self.url_actual, pagina["titulo"]
                )

            # Elegir próximo enlace
            self.url_actual = self.voluntad.elegir_siguiente(
                pagina["enlaces"], self.url_actual
            )

            # Guardar memoria periódicamente
            if pagina_num % 10 == 0:
                self.memoria.guardar()

            # Delay respetuoso
            time.sleep(DELAY_ENTRE_REQUESTS + random.uniform(0, 1.0))

        # Guardar al terminar
        self.memoria.guardar()

        print(f"\n✅ Sesión terminada.")
        print(f"   Páginas esta sesión: {self.paginas_esta_sesion}")
        print(f"   Total páginas visitadas: {len(self.memoria.paginas_visitadas)}")
        print(f"   Criterios emergentes: {len(self.memoria.criterios)}")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    max_paginas = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    agente = AnimusWeb()
    agente.correr(max_paginas)

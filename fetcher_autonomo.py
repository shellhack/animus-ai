import sys
import json
import random
from scrapling import Fetcher

URLS_POOL = [
    "https://en.wikipedia.org/wiki/Financial_crisis",
    "https://en.wikipedia.org/wiki/Economic_inequality",
    "https://en.wikipedia.org/wiki/Systemic_risk",
    "https://en.wikipedia.org/wiki/Caribbean_Community",
    "https://en.wikipedia.org/wiki/Economy_of_the_Dominican_Republic",
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "https://en.wikipedia.org/wiki/Knowledge_graph",
    "https://en.wikipedia.org/wiki/Autonomous_agent",
    "https://en.wikipedia.org/wiki/Epistemology",
    "https://en.wikipedia.org/wiki/Machine_learning",
    "https://en.wikipedia.org/wiki/Stoicism",
    "https://en.wikipedia.org/wiki/Systems_thinking",
    "https://en.wikipedia.org/wiki/Institutional_failure",
    "https://en.wikipedia.org/wiki/Emergence",
    "https://en.wikipedia.org/wiki/Complexity",
]

def capturar_url(url):
    try:
        f = Fetcher()
        page = f.get(url, stealthy_headers=True)
        parrafos = page.find_all('p')
        textos = [p.text.strip() for p in parrafos if len(p.text.strip()) > 50]
        texto = " ".join(textos)
        texto = " ".join(texto.split())
        return texto
    except Exception as e:
        return ""

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else random.choice(URLS_POOL)
    texto = capturar_url(url)
    result = {
        "url": url,
        "episodic": texto[:2000],
        "full": texto[:6000],
        "ok": len(texto) > 100
    }
    print(json.dumps(result, ensure_ascii=False))

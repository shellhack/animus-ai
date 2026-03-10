import requests
from bs4 import BeautifulSoup
import time

# Objetivo: Documentación de Fuel
BASE_URL = "https://docs.fuel.network/"

def auditar_docs(url):
    print(f"🔍 ANIMUS analizando: {url}")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Buscar todos los enlaces
        links = soup.find_all('a', href=True)
        print(f"🔗 Encontrados {len(links)} enlaces. Verificando integridad...")
        
        for link in links:
            href = link['href']
            # Normalizar URL
            full_url = href if href.startswith('http') else BASE_URL + href
            
            try:
                check = requests.head(full_url, timeout=5)
                if check.status_code == 404:
                    print(f"🚨 BUG DETECTADO: Enlace roto en {full_url}")
            except:
                pass # Errores de conexión menores
                
    except Exception as e:
        print(f"❌ Error de acceso: {e}")

if __name__ == "__main__":
    auditar_docs(BASE_URL)
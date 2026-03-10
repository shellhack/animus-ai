from scrapling import fetch

def capturar_realidad(url):
    # El modo 'stealth' bypassa Cloudflare y torniquetes automáticamente
    page = fetch(url, stealth=True)
    
    # Scrapling no necesita selectores rígidos si usas el modo IA
    # Extraemos el texto limpio para el Grafo de Sabiduría
    return page.text

if __name__ == "__main__":
    # Ejemplo: Validando el presupuesto de RD en tiempo real
    print(capturar_realidad("https://www.dgii.gov.do/"))
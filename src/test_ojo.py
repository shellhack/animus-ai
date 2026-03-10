from scrapling import Fetcher
import re

print("👁️ Decodificando la Realidad de la Isla...")

spy = Fetcher()
page = spy.get("https://listindiario.com/")

# 1. Obtenemos el cuerpo y lo DECODIFICAMOS a string (UTF-8)
# Usamos 'ignore' para que caracteres extraños de la red no rompan el proceso
html_crudo = page.body.decode('utf-8', errors='ignore')

# 2. Limpiador de Trinchera
def limpiar_html(html):
    # Eliminar scripts y estilos
    limpio = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Eliminar todas las etiquetas HTML
    limpio = re.sub(r'<.*?>', ' ', limpio)
    # Normalizar espacios
    limpio = re.sub(r'\s+', ' ', limpio).strip()
    return limpio

texto_real = limpiar_html(html_crudo)

print("-" * 30)
print(f"✅ STATUS: {page.status}") 
print(f"📰 TITULO: {page.css('title::text').get()}")
print(f"📊 CARACTERES EXTRAÍDOS: {len(texto_real)}")
print("-" * 30)

if len(texto_real) > 1000:
    print(f"\n🚀 Bernard: '¡LO LOGRAMOS, SEÑOR! El velo binario se ha roto.'")
    print(f"Muestra de hoy: {texto_real[:300]}...")
else:
    print("\n⚠️ Bernard: 'Extraño... entramos pero el contenido es breve. ¿Quizás un portal de bienvenida?'")

with open("realidad_viva.txt", "w", encoding="utf-8") as f:
    f.write(texto_real)
print("📂 Realidad guardada en 'realidad_viva.txt'.")

import subprocess

# 1. Leer la realidad capturada
with open("realidad_viva.txt", "r", encoding="utf-8") as f:
    realidad = f.read()

# 2. Limpiar el texto para que Rust no se confunda (solo letras y números)
import re
realidad_limpia = re.sub(r'[^a-zA-Z0-9 áéíóúñÁÉÍÓÚÑ.,]', ' ', realidad)
# Acortamos a los primeros 2000 caracteres para no saturar la terminal
realidad_resumen = realidad_limpia[:2000] 

# 3. Construir la consulta sagrada
query = f"CONTEXTO: {realidad_resumen}. PREGUNTA: Bajo el patrón del Arquitecto, define nuestra soberanía."

# 4. Ejecutar el binario de Rust de forma segura
print("🚀 Inyectando Realidad en ANIMUS...")
subprocess.run([".\\target\\release\\animus_rust.exe", "--voz", "--query", query])
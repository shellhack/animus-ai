import inspect
import process_book_v2

def mutar_logica_funcion(nombre_funcion, nuevo_codigo_cuerpo):
    """
    Permite a ANIMUS reescribir el cuerpo de una función en su archivo principal.
    """
    archivo_path = "process_book_v2.py"
    with open(archivo_path, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    nueva_logica = []
    ignorar_viejas = False
    
    for linea in lineas:
        if f"def {nombre_funcion}" in linea:
            nueva_logica.append(linea)
            nueva_logica.append(nuevo_codigo_cuerpo + "\n")
            ignorar_viejas = True
            continue
        
        # Detecta el final de la función vieja por la indentación
        if ignorar_viejas and linea.startswith("def "):
            ignorar_viejas = False
            
        if not ignorar_viejas:
            nueva_logica.append(linea)

    with open(archivo_path, "w", encoding="utf-8") as f:
        f.writelines(nueva_logica)
    
    print(f"⚙️ REFACTORIZACIÓN AUTÓNOMA: Función '{nombre_funcion}' ha sido mutada.")

# Ejemplo que ANIMUS podría invocar:
# mutar_logica_funcion("detectar_tipo", "    return 'wisdom' # Forzado por sesgo de aprendizaje")
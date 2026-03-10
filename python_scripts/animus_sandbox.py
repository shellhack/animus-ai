import ast

def validar_codigo(codigo_propuesto):
    """Verifica que el código propuesto no tenga errores de sintaxis antes de aplicarlo."""
    try:
        ast.parse(codigo_propuesto)
        return True
    except SyntaxError as e:
        print(f"❌ ERROR DE SINTAXIS DETECTADO: {e}")
        return False

def proponer_mutacion(nombre_archivo, funcion_objetivo, nueva_logica):
    if validar_codigo(nueva_logica):
        print(f"✅ Código validado. Procediendo a mutar {funcion_objetivo}...")
        # Aquí llamaríamos a la función de escritura física
    else:
        print("⚠️ Mutación rechazada: El código propuesto rompería el sistema.")
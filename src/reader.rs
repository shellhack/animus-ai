use std::fs;

pub fn leer_propio_codigo() -> String {
    // Leemos el corazón del sistema
    let paths = vec!["src/main.rs", "src/memory.rs", "src/brain.rs"];
    let mut codigo_completo = String::new();

    for path in paths {
        if let Ok(contenido) = fs::read_to_string(path) {
            codigo_completo.push_str(&format!("\n--- ARCHIVO: {} ---\n{}", path, contenido));
        }
    }
    codigo_completo
}
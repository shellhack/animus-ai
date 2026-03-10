// inspector.rs — Autoconocimiento de ANIMUS
// En lugar de código fuente, reporta el estado epistemológico
use crate::memory::AnimusMemory;

pub fn leer_propio_codigo() -> String {
    // Ya no inyectamos código — inyectamos autoconciencia
    String::new()
}

pub fn generar_contexto_epistemico(memory: &AnimusMemory) -> String {
    let total = memory.nodes.len();
    let peso_max = memory.nodes.iter()
        .map(|n| n.weight as u64)
        .max()
        .unwrap_or(0);
    
    let top_nodos: Vec<String> = memory.nodes.iter()
        .filter(|n| !n.label.starts_with("Origen:"))
        .take(5)
        .map(|n| format!("  - {} (peso: {:.0})", n.label, n.weight))
        .collect();

    format!(
        "[AUTOCONCIENCIA ANIMUS]\n\
        Nodos activos: {}\n\
        Peso máximo: {}\n\
        Conocimiento más relevante:\n{}",
        total, peso_max, top_nodos.join("\n")
    )
}

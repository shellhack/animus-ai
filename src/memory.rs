// src/memory.rs
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use rayon::prelude::*;

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct SerializableNode {
    pub label: String,
    pub content: String,
    pub era: String,
    pub weight: f64,
    pub connections: u32,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct SerializableEdge {
    pub from: usize,
    pub to: usize,
    pub weight: f64,
}

#[derive(Serialize, Deserialize)]
pub struct AnimusMemory {
    pub nodes: Vec<SerializableNode>,         // <--- Añadido pub
    pub edges: Vec<SerializableEdge>,         // <--- Añadido pub
    pub seed_query: String,                   // <--- Añadido pub
    pub cycle_count: u32,                     // <--- Añadido pub
    pub last_query: String,                   // <--- Añadido pub
    pub repetition_count: u32,                 // <--- Añadido pub
}

// Estructura para no perder el formato de Claude
#[derive(Serialize, Deserialize)]
pub struct BusinessMemory {
    pub conexiones: std::collections::HashMap<String, f64>,
}

impl AnimusMemory {
    pub fn buscar_contradicciones(&self, query: &str) -> Vec<String> {
        // Escaneo paralelo en los 757 nodos usando los núcleos del i5
        self.nodes.par_iter()
            .filter(|n| n.content.contains(query) && n.content.contains("error"))
            .map(|n| n.content.clone())
            .collect()
    }
    /// Carga la memoria de negocio (la sabiduría de los 11 días)
    pub fn load_business_memory() -> Option<BusinessMemory> {
        let path = "memoria_business.json";
        if Path::new(path).exists() {
            let data = fs::read_to_string(path).ok()?;
            serde_json::from_str(&data).ok()
        } else {
            None
        }
    }
    pub fn load() -> std::io::Result<Self> {
        let path = "animus_memory.json";
        
        println!("🔍 Buscando rastro en: {}", path);

        if Path::new(path).exists() {
            let json_data = fs::read_to_string(path)?;
            println!("📄 Archivo leído. Tamaño: {} bytes", json_data.len());

            // Intentamos ver la estructura cruda
            let v: serde_json::Value = serde_json::from_str(&json_data).unwrap_or_default();
            
            if let Some(nodes_array) = v["nodes"].as_array() {
                println!("💡 ¡Encontrados {} nodos en el JSON!", nodes_array.len());
                
                let mut memoria = Self::new("sabiduría milenaria");
                for n in nodes_array {
                    memoria.nodes.push(SerializableNode {
                        label: n["label"].as_str().unwrap_or("").to_string(),
                        content: n["content"].as_str().unwrap_or("").to_string(),
                        era: n["era"].as_str().unwrap_or("").to_string(),
                        weight: n["weight"].as_f64().unwrap_or(0.0),
                        connections: n["connections"].as_u64().unwrap_or(0) as u32,
                    });
                }
                return Ok(memoria);
            } else {
                println!("❌ Error: El JSON no tiene una lista llamada 'nodes'.");
            }
        } else {
            println!("❌ Error: El archivo {} NO EXISTE en la ruta actual.", path);
        }

        Ok(Self::new("Nueva Era"))
}

    pub fn save(&self) -> std::io::Result<()> {
        let json = serde_json::to_string_pretty(self).unwrap();
        fs::write("animus_memory.json", json)
    }

    pub fn new(seed: &str) -> Self { // <--- Añadido pub para que main pueda crearlo
        AnimusMemory {
            nodes: vec![],
            edges: vec![],
            seed_query: seed.to_string(),
            cycle_count: 0,
            last_query: String::new(),
            repetition_count: 0,
        }
    }

    pub fn agregar_recuerdo(&mut self, contenido: &str, label: &str) {
        let nuevo_nodo = SerializableNode {
            label: label.to_string(),
            content: contenido.to_string(),
            era: chrono::Local::now().format("%Y-%m").to_string(),
            weight: 1.0,
            connections: 1, // El primer vínculo es con su propia creación
        };
        
        self.nodes.push(nuevo_nodo);
        println!("📝 Nodo {} integrado en el núcleo de memoria.", self.nodes.len());
    }

    pub fn buscar_indice_por_label(&self, objetivo: &str) -> Option<usize> {
        self.nodes.iter().position(|n| n.label.contains(objetivo))
    }

    pub fn conectar_nodos(&mut self, desde: usize, hasta: usize, peso: f64) {
        let nueva_conexion = SerializableEdge {
            from: desde,
            to: hasta,
            weight: peso,
        };
        self.edges.push(nueva_conexion);
        
        // Incrementamos el contador de conexiones en los nodos afectados
        if let Some(n) = self.nodes.get_mut(desde) { n.connections += 1; }
        if let Some(n) = self.nodes.get_mut(hasta) { n.connections += 1; }
    }
}
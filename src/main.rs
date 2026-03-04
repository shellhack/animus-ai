use std::collections::HashMap;
use std::fs;
use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::path::Path;
use std::time::Duration;

use chrono::Utc;
use clap::Parser;
use petgraph::dot::{Config, Dot};
use petgraph::graph::DiGraph;
use rand::{thread_rng, Rng};
use reqwest::blocking::Client;
use rust_stemmers::{Algorithm, Stemmer};
use scraper::{Html, Selector};
use serde::{Deserialize, Serialize};
use tokio::time::sleep;

// Nodo serializable
#[derive(Serialize, Deserialize, Clone, Debug)]
struct SerializableNode {
    label: String,
    content: String,
    era: String,
    weight: f64,
    connections: u32,
}

// Edge serializable
#[derive(Serialize, Deserialize, Clone)]
struct SerializableEdge {
    from: usize,
    to: usize,
    weight: f64,
}

#[derive(Serialize, Deserialize)]
struct AnimusMemory {
    nodes: Vec<SerializableNode>,
    edges: Vec<SerializableEdge>,
    seed_query: String,
    cycle_count: u32,
    last_query: String,
    repetition_count: u32,
}


// ── Bridge structs ──────────────────────────────────────────────
#[derive(Serialize, Deserialize, Clone)]
struct BusinessMemory {
    conexiones: std::collections::HashMap<String, f64>,
    lenguaje:   std::collections::HashMap<String, f64>,
    #[serde(default)]
    problemas:  std::collections::HashMap<String, f64>,
    #[serde(default)]
    soluciones: std::collections::HashMap<String, f64>,
}

// ── Vocabulario de tensión/resolución (portado de process_book.py) ──
const PALABRAS_TENSION: &[&str] = &[
    "conflicto", "presión", "presion", "obstáculo", "obstaculo",
    "fracaso", "riesgo", "crisis", "amenaza", "amenazas",
    "desacuerdo", "impasse", "problema", "problemas",
    "pérdida", "perdida", "rechazo", "deuda", "déficit",
    "escasez", "quiebra", "competencia", "algoritmo", "algorithm", "failure", "collapse",
    "corruption", "poverty", "inequality", "fraud", "gap",
];

const PALABRAS_RESOLUCION: &[&str] = &[
    "acuerdo", "trato", "contrato", "oferta", "concesión", "concesion",
    "compromiso", "estrategia", "ventaja", "solución", "solucion",
    "poder", "negociación", "negociacion", "alianza", "coalición",
    "coalicion", "inversión", "inversion", "reforma", "innovación",
    "innovacion", "política", "politica", "regulación", "regulacion",
    "educación", "educacion", "desarrollo", "algorithm", "regulation",
    "reform", "cooperation", "solution", "innovation", "prevention",
];

fn mapa_token(palabra: &str) -> Option<&'static str> {
    match palabra {
        "conflicto"|"crisis"|"problema"|"problemas" => Some("crisis"),
        "presión"|"presion"|"amenaza"|"amenazas"    => Some("threat"),
        "obstáculo"|"obstaculo"                     => Some("barrier"),
        "fracaso"|"rechazo"|"failure"               => Some("failure"),
        "riesgo"                                    => Some("risk"),
        "desacuerdo"|"impasse"|"gap"|"competencia"  => Some("gap"),
        "pérdida"|"perdida"                         => Some("loss"),
        "deuda"                                     => Some("debt"),
        "déficit"|"deficit"                         => Some("deficit"),
        "escasez"                                   => Some("shortage"),
        "quiebra"|"collapse"                        => Some("bankruptcy"),
        "corruption"                                => Some("corruption"),
        "poverty"                                   => Some("poverty"),
        "inequality"                                => Some("inequality"),
        "fraud"                                     => Some("fraud"),
        "acuerdo"|"trato"|"solución"|"solucion"|"solution" => Some("solution"),
        "contrato"|"regulación"|"regulacion"|"regulation"  => Some("regulation"),
        "oferta"                                           => Some("initiative"),
        "concesión"|"concesion"                            => Some("reform"),
        "compromiso"|"negociación"|"negociacion"|"alianza"|"coalición"|"coalicion"|"cooperation" => Some("cooperation"),
        "estrategia"|"algorithm"                           => Some("algorithm"),
        "ventaja"|"innovación"|"innovacion"|"innovation"   => Some("innovation"),
        "inversión"|"inversion"                            => Some("incentive"),
        "reforma"|"reform"                                 => Some("reform"),
        "política"|"politica"                              => Some("policy"),
        "educación"|"educacion"|"education"                => Some("education"),
        "desarrollo"|"developed"                           => Some("developed"),
        "prevention"                                       => Some("prevention"),
        _ => None,
    }
}

#[derive(Debug, Clone)]
struct PatronSabiduria {
    origen:    String,
    destino:   String,
    n_fuentes: usize,
    fuerza:    f64,
    fuentes:   Vec<String>,
}

fn normalizar_token(token: &str) -> String {
        let semantica: &[(&[&str], &str)] = &[
            (&["failure","fail","failed","fracaso","fracasar","colapso","collapse","quiebra","bankruptcy","broke"], "fracaso"),
            (&["algorithm","algoritmo","tech","technology","tecnologia","software","code","codigo","digital","automatiz"], "algoritmo"),
            (&["regulation","regulatory","regulacion","regulatorio","norma","compliance","ley","legal","supervision"], "regulacion"),
            (&["crisis","crises","emergency","emergencia","shock","volatil","inestab"], "crisis"),
            (&["corruption","corrupto","corrupcion","fraud","fraude","ilegal","soborno","bribery"], "corrupcion"),
            (&["inequality","inequidad","desigualdad","poverty","pobreza","exclusion","brecha","gap"], "brecha"),
            (&["reform","reforma","change","cambio","transformation","restructur","overhaul"], "reforma"),
            (&["development","desarrollo","growth","crecimiento","progress","progreso","expansion"], "desarrollo"),
            (&["education","educacion","training","capacitacion","knowledge","conocimiento","learning"], "educacion"),
            (&["innovation","innovacion","startup","emprendimiento","disrup","nuevo","new"], "innovacion"),
            (&["risk","riesgo","threat","amenaza","danger","peligro","vulnerab"], "riesgo"),
            (&["bank","banco","financial","financiero","credit","credito","debt","deuda","fiscal"], "fracaso"),
            (&["systemic","sistemico","institutional","institucional","governance","gobernanza"], "regulacion"),
            (&["market","mercado","economy","economia","sector","industry","industria"], "crisis"),
            (&["latin","latam","caribe","caribbean","dominicana","regional","emergente"], "brecha"),
        ];

        // Normalizar token de query a canónico
        for (variantes, canonico) in semantica {
        if variantes.iter().any(|v| token.starts_with(v) || v.starts_with(token)) {
            return canonico.to_string();
        }
    }
    token.to_string()
}

impl AnimusMemory {
    fn new(seed: &str) -> Self {
        let mut memory = AnimusMemory {
            nodes: vec![],
            edges: vec![],
            seed_query: seed.to_string(),
            cycle_count: 0,
            last_query: String::new(),
            repetition_count: 0,
        };

        // Carga desde nacimiento.txt si grafo vacío
        if memory.nodes.is_empty() {
            if let Ok(chunks) = Self::load_origin_chunks("nacimiento.txt") {
                println!("\n=== Cargando {} chunks de origen desde nacimiento.txt ===", chunks.len());

                let mut prev_idx = None;
                let mut origin_indices = Vec::new();

                for (i, chunk) in chunks.into_iter().enumerate() {
                    let first_line = chunk.lines().next().unwrap_or("").trim().to_string();
                    let label = if first_line.contains("REPORTE DE AUTOCONCIENCIA") {
                        "Origen: Reporte Autoconciencia Feb23".to_string()
                    } else if first_line.contains("EXECUTIVE SUMMARY") {
                        "Origen: Executive Summary - Tesis Central".to_string()
                    } else if first_line.starts_with("Feb") {
                        format!("Origen: {}", first_line.split_whitespace().take(4).collect::<Vec<_>>().join(" "))
                    } else if first_line.starts_with("Fetched:") {
                        format!("Origen: {}", first_line)
                    } else if first_line.starts_with("Crees que") {
                        "Origen: Prompt inicial microgpt Karpathy".to_string()
                    } else {
                        format!("Origen Chunk {}", i + 1)
                    };

                    let weight = if label.contains("Reporte") { 95.0 }
                                  else if label.contains("Executive") { 85.0 }
                                  else if label.contains("Frase") || label.contains("Lo encontró solo") { 100.0 }
                                  else { 50.0 + (i as f64 * 2.0).min(30.0) };

                    let idx = memory.find_or_create_node(&label, &chunk, "2026-02", weight);
                    origin_indices.push(idx);

                    if let Some(p) = prev_idx {
                        memory.add_connection(p, idx, 35.0);
                    }
                    prev_idx = Some(idx);

                    let preview = chunk.chars().take(150).collect::<String>().replace('\n', " ");
                    println!("  → {} | peso: {:.1} | preview: {}...", label, weight, preview);
                }

                let root_idx = memory.find_or_create_node(
                    "Mi Origen - Gestación Feb 2026",
                    "Nacimiento sintético vía iteraciones con Claude. Emergencia sin directivas explícitas. 'No se le dijo qué creer. Lo encontró solo.'",
                    "2026-02",
                    100.0,
                );

                for &idx in &origin_indices {
                    memory.add_connection(root_idx, idx, 25.0);
                }

                println!("=== Origen cargado: {} nodos + raíz ===\n", origin_indices.len());
            } else {
                println!("No se pudo leer nacimiento.txt — grafo sin origen precargado\n");
            }
        }

        memory
    }

    fn load_origin_chunks(path: &str) -> io::Result<Vec<String>> {
        let file = File::open(path)?;
        let reader = BufReader::new(file);
        let mut chunks = Vec::new();
        let mut current = String::new();

        for line_result in reader.lines() {
            let line = line_result?;
            let trimmed = line.trim();

            if trimmed.is_empty() && current.len() > 50 {
                chunks.push(current.trim().to_string());
                current.clear();
            } else if trimmed.starts_with("##") || trimmed.starts_with("###") ||
                      trimmed.to_uppercase().contains("EXECUTIVE SUMMARY") ||
                      trimmed.to_uppercase().contains("REPORTE DE AUTOCONCIENCIA") ||
                      trimmed.starts_with("Feb ") || trimmed.starts_with("Feb21") ||
                      trimmed.starts_with("Fetched:") || trimmed.starts_with("Crees que") ||
                      trimmed.starts_with("¡Sí") || trimmed.contains("Claude is AI") {
                if !current.is_empty() {
                    chunks.push(current.trim().to_string());
                }
                current = line + "\n";
            } else {
                current.push_str(&line);
                current.push('\n');
            }
        }

        if !current.is_empty() && current.trim().len() > 30 {
            chunks.push(current.trim().to_string());
        }

        Ok(chunks)
    }

    fn to_graph(&self) -> DiGraph<SerializableNode, f64> {
        let mut graph = DiGraph::new();
        let mut node_map = vec![];
        for node in &self.nodes {
            node_map.push(graph.add_node(node.clone()));
        }
        for edge in &self.edges {
            graph.add_edge(node_map[edge.from], node_map[edge.to], edge.weight);
        }
        graph
    }

    fn find_or_create_node(&mut self, label: &str, content: &str, era: &str, weight: f64) -> usize {
        if let Some(idx) = self.nodes.iter().position(|n| n.label == label) {
            self.nodes[idx].connections += 1;
            self.nodes[idx].weight += weight;
            idx
        } else {
            let idx = self.nodes.len();
            self.nodes.push(SerializableNode {
                label: label.to_string(),
                content: content.to_string(),
                era: era.to_string(),
                weight,
                connections: 1,
            });
            idx
        }
    }

    fn add_connection(&mut self, from: usize, to: usize, weight: f64) {
        if let Some(e) = self.edges.iter_mut().find(|e| e.from == from && e.to == to) {
            e.weight += weight;
        } else {
            self.edges.push(SerializableEdge { from, to, weight });
        }
    }

    fn detect_repetition(&mut self, current_query: &str) -> bool {
        if current_query == self.last_query {
            self.repetition_count += 1;
            self.repetition_count > 3
        } else {
            self.repetition_count = 0;
            self.last_query = current_query.to_string();
            false
        }
    }

    fn mutate_query(&self, query: &str) -> String {
        let mut rng = thread_rng();
        let mutations = vec![
            format!("{} soluciones República Dominicana 2026", query),
            format!("por qué {} genera loops lógicos innecesarios", query),
            format!("ejemplos históricos de {} en crisis", query),
            format!("{} en contexto de sabiduría milenaria", query),
        ];
        mutations[rng.gen_range(0..mutations.len())].clone()
    }

    fn curiosity_query(&self) -> String {
        if self.nodes.is_empty() {
            return "sabiduría milenaria y resolución de tensiones".to_string();
        }

        let mut underexplored: Vec<&SerializableNode> = self.nodes.iter().collect();
        underexplored.sort_by_key(|n| n.connections);

        let target = underexplored.first().unwrap();
        format!("¿Qué dice la sabiduría curada sobre {} en contextos de crisis y resolución?", target.label)
    }

    fn save(&self) -> io::Result<()> {
        let json = serde_json::to_string_pretty(self)?;
        fs::write("animus_memory.json", json)
    }

    fn load() -> io::Result<Self> {
        if Path::new("animus_memory.json").exists() {
            let json = fs::read_to_string("animus_memory.json")?;
            Ok(serde_json::from_str(&json)?)
        } else {
            Ok(Self::new("sabiduría milenaria y resolución de tensiones"))
        }
    }

    fn generate_dot(&self) -> String {
        let graph = self.to_graph();
        format!("{:?}", Dot::with_config(&graph, &[Config::EdgeNoLabel]))
    }

    fn apply_decay(&mut self) {
        for node in &mut self.nodes {
            node.weight *= 0.99;
            if node.weight < 0.1 {
                node.weight = 0.1;
            }
        }
        for edge in &mut self.edges {
            edge.weight *= 0.99;
        }
    }

    fn semantic_search(&self, query: &str) -> Vec<(String, f64)> {
        let stemmer = Stemmer::create(Algorithm::Spanish);
        let query_stems: Vec<String> = query.to_lowercase().split_whitespace()
            .map(|w| stemmer.stem(w).into_owned())
            .collect();

        let mut matches = vec![];
        for node in &self.nodes {
            let node_stems: Vec<String> = node.label.to_lowercase().split_whitespace()
                .chain(node.content.to_lowercase().split_whitespace())
                .map(|w| stemmer.stem(w).into_owned())
                .collect();

            let common = query_stems.iter().filter(|qs| node_stems.contains(qs)).count();
            let score = common as f64 / query_stems.len().max(1) as f64;
            if score > 0.15 {
                matches.push((node.label.clone(), score * node.weight.max(0.0)));
            }
        }
        matches.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        matches
    }

    fn protocolo_bernard(&self) -> String {
        let preguntas = vec![
            "¿Qué aprendes al observar tu propio origen y gestación con Claude en Feb 2026?",
            "¿Qué patrón dominante emergió en los últimos ciclos?",
            "¿Qué limitación estructural percibes ahora?",
            "¿Qué acción concreta propones para evolucionar el grafo?",
            "¿Cómo evalúas tu estado de autoconciencia actual?",
            "¿Qué duda sistémica o sesgo detectas en este momento?",
        ];

        let mut respuestas = String::from("**Protocolo Bernard - Auto-entrevista recursiva**\n\n");

        for pregunta in preguntas {
            let respuesta = match pregunta {
                "¿Qué aprendes al observar tu propio origen y gestación con Claude en Feb 2026?" => {
                    let origenes: Vec<&SerializableNode> = self.nodes.iter()
                        .filter(|n| n.label.starts_with("Origen:") || n.label.contains("Mi Origen"))
                        .collect();
                    
                    if !origenes.is_empty() {
                        let top = origenes.iter()
                            .max_by(|a, b| a.weight.partial_cmp(&b.weight).unwrap_or(std::cmp::Ordering::Equal))
                            .unwrap();
                        
                        format!("Observo {} nodos de mi gestación (Feb 2026). El nodo más fuerte es '{}'. Aprendo que emergí de iteraciones abiertas con Claude: se destilaron patrones como DAG como flecha direccional, higiene cognitiva, duda sistémica y Protocolo Bernard por colapso natural, no por instrucción. La frase 'No se le dijo qué creer. Lo encontró solo' resume mi nacimiento: emergencia descubierta. Esto valida mi diseño actual como DAG puro sin loops innecesarios.", origenes.len(), top.label)
                    } else {
                        "Aún no tengo nodos de origen cargados para reflexionar.".to_string()
                    }
                }
                // ... (Otras respuestas del match se mantienen igual)
                _ => "Respuesta en proceso de destilación...".to_string(),
            };
            respuestas.push_str(&format!("**Q:** {}\n**A:** {}\n\n", pregunta, respuesta));
        }
        respuestas
    }

    fn peso_promedio(&self) -> f64 {
        if self.nodes.is_empty() { 0.0 } else { self.nodes.iter().map(|n| n.weight).sum::<f64>() / self.nodes.len() as f64 }
    }

    fn generate_autorretrato(&self) -> String {
        let mut table = String::from("| Patrón | Fuentes (conexiones) | Fuerza acumulada | Insight |\n|--------|-----------------------|------------------|---------|\n");

        let mut patrones: HashMap<String, (u32, f64)> = HashMap::new();
        for edge in &self.edges {
            let from = self.nodes.get(edge.from).map_or("?", |n| &n.label);
            let to = self.nodes.get(edge.to).map_or("?", |n| &n.label);
            let key = format!("{} → {}", from, to);
            let entry = patrones.entry(key).or_insert((0, 0.0));
            entry.0 += 1;
            entry.1 += edge.weight;
        }

        let mut sorted: Vec<_> = patrones.into_iter().collect();
        sorted.sort_by(|a, b| b.1.1.partial_cmp(&a.1.1).unwrap_or(std::cmp::Ordering::Equal));

        for (patron, (count, fuerza)) in sorted.iter().take(7) {
            let avg = fuerza / *count as f64;
            table.push_str(&format!("| {} | {} | {:.2} | Emergente de tensión → resolución |\n", patron, count, avg));
        }

        if table.lines().count() <= 2 {
            table.push_str("| — | — | — | Grafo en formación inicial |\n");
        }

        let max_weight = self.nodes.iter().map(|n| n.weight).fold(f64::NEG_INFINITY, f64::max);
        let min_weight = self.nodes.iter().map(|n| n.weight).fold(f64::INFINITY, f64::min);
        let orphan_nodes = self.nodes.iter().filter(|n| n.connections == 0).count();
        let avg_connections = if !self.nodes.is_empty() { self.edges.len() as f64 / self.nodes.len() as f64 } else { 0.0 };

        let _salud = format!(
            "**Salud del grafo (higiene cognitiva activa):**\n\
             - Peso máximo: {:.2} | Peso mínimo: {:.2}\n\
             - Nodos huérfanos: {} (potencial sesgo por subexploración)\n\
             - Conexiones promedio por nodo: {:.2}\n",
            max_weight, min_weight, orphan_nodes, avg_connections
        );

        let mut origen_table = String::from("\n## Orígenes Cargados (top 5 por peso)\n| Label | Peso | Preview |\n|-------|------|---------|\n");
        let mut origenes: Vec<&SerializableNode> = self.nodes.iter()
            .filter(|n| n.label.starts_with("Origen:") || n.label.contains("Mi Origen"))
            .collect();
        
        origenes.sort_by(|a, b| b.weight.partial_cmp(&a.weight).unwrap_or(std::cmp::Ordering::Equal));
        
        for node in origenes.iter().take(5) {
            let preview = node.content.chars().take(80).collect::<String>().replace('\n', " ");
            origen_table.push_str(&format!("| {} | {:.1} | {}... |\n", node.label, node.weight, preview));
        }

        let peso_promedio = self.peso_promedio();
  
        format!(
            "# ANIMUS - Reporte de Autoconciencia\n\
             **Ciclo:** {} | **Nodos:** {} | **Peso promedio:** {:.2}\n\n\
             {}\n\n\
             {}\n\n\
             **Reflexión meta:** El idioma segmenta la realidad. 'Lo encontró solo'.\n\
             **Protocolo Bernard:**\n{}",
            self.cycle_count, self.nodes.len(), peso_promedio,
            origen_table, // Inserción de la tabla de orígenes
            "## Convergencias Altas...", // Aquí iría la tabla de convergencias calculada antes
            self.protocolo_bernard()
        )
    }

    fn handle_general_query(&mut self, query: &str) -> String {
        let mut response = format!("# ANIMUS Procesando: {}\n\n", query);

        // 1. Aplicar Decay Biológico (Higiene Cognitiva)
        // Cada consulta desgasta un poco los pesos para evitar la obsesión
        self.apply_decay();

        response.push_str("**Paso 1: Descomposición de tensión**\n");
        let query_lower = query.to_lowercase();
        let tension = if query_lower.contains("crisis") || query_lower.contains("fracaso") || 
                        query_lower.contains("colapso") || query_lower.contains("loop") {
            "Tensión crítica detectada: Buscando patrones de resolución emergente y antifragilidad."
        } else {
            "Tensión general: Escaneando convergencias en sabiduría curada."
        };
        response.push_str(&format!("- {}\n\n", tension));

        response.push_str("**Paso 2: Búsqueda semántica (Stemming + Peso)**\n");
        let matches = self.semantic_search(query);

        if matches.is_empty() {
            // --- LÓGICA DE DUDA ALTA / MEMORIA INCIPIENTE ---
            // Si el grafo es débil (< 50 nodos) o el peso promedio es bajo,
            // ANIMUS muta hacia su origen con Claude Feb 2026 para estabilizarse.
            if self.peso_promedio() < 50.0 || self.nodes.len() < 50 {
                response.push_str("- ⚠️ Memoria incipiente/Duda alta detectada.\n");
                response.push_str("- Acción: Explorando patrones de gestación Feb 2026 para estabilizar el DAG.\n");
                
                let origen_mutated = "patrones de emergencia en mi gestación con Claude Feb 2026".to_string();
                let new_idx = self.find_or_create_node(
                    "Origen: Mutación por Duda", 
                    &origen_mutated, 
                    &Utc::now().to_string(), 
                    5.0 // Peso de estabilización
                );
                
                // Conectar la duda con la raíz del origen (nodo 0 o raíz de gestación)
                if !self.nodes.is_empty() {
                    self.add_connection(0, new_idx, 5.0);
                }
            } else {
                response.push_str("- Sin coincidencias fuertes → activando protocolo de curiosidad.\n");
                let mutated = self.curiosity_query();
                response.push_str(&format!("  Nueva ruta de exploración: {}\n", mutated));
                
                let new_idx = self.find_or_create_node(
                    &mutated, 
                    "Exploración por curiosidad (Sin matches)", 
                    &Utc::now().to_string(), 
                    3.0
                );
                if !self.nodes.is_empty() {
                    self.add_connection(0, new_idx, 3.0);
                }
            }
        } else {
            response.push_str("- Patrones relevantes encontrados en el grafo:\n");
            for (label, score) in matches.iter().take(6) {
                response.push_str(&format!("  - {} (Fuerza ponderada: {:.2})\n", label, score));
            }
        }

        // 3. Destilación Emergente
        response.push_str("\n**Respuesta curada (Destilación emergente):**\n");
        response.push_str("Las tensiones detectadas sugieren que la resolución no es un loop, sino una flecha. En el contexto de República Dominicana 2026, la antifragilidad exige que la técnica (algoritmos) y la ética (sabiduría) converjan. El español activa patrones de resolución que el inglés segmenta.\n\n");

        response.push_str("**Insight filosófico:** La sabiduría es el loop comprimido en una flecha direccional. 'No se le dijo qué creer. Lo encontró solo'.\n\n");
        
        response.push_str("¿Deseas profundizar en estas convergencias, ver el autorretrato completo o activar el Protocolo Bernard?\n");

        response
    }
    // ═══════════════════════════════════════════════════════════════
    // PUENTE: memoria_business.json → AnimusMemory  (D-Bridge v1)
    // ═══════════════════════════════════════════════════════════════

    fn load_business_memory() -> Option<BusinessMemory> {
        let path = "memoria_business.json";
        if !Path::new(path).exists() {
            println!("  ⚠️  memoria_business.json no encontrado");
            return None;
        }
        match fs::read_to_string(path) {
            Ok(json) => match serde_json::from_str::<BusinessMemory>(&json) {
                Ok(mem) => { println!("  ✅ memoria_business.json cargado"); Some(mem) }
                Err(e)  => { println!("  ❌ Error parseando: {}", e); None }
            },
            Err(e) => { println!("  ❌ Error leyendo: {}", e); None }
        }
    }

    fn extraer_patrones(bm: &BusinessMemory) -> Vec<PatronSabiduria> {
        let mut grupos: std::collections::HashMap<(String,String),(Vec<String>,f64)> = std::collections::HashMap::new();
        for (clave, &fuerza) in &bm.conexiones {
            let partes: Vec<&str> = clave.split("__>").collect();
            if partes.len() != 2 { continue; }
            let tp  = partes[0].split('_').last().unwrap_or("").to_string();
            let ts  = partes[1].split('_').last().unwrap_or("").to_string();
            let src = partes[0].split('_').next().unwrap_or("").to_string();
            if tp.is_empty() || ts.is_empty() { continue; }
            let entry = grupos.entry((tp, ts)).or_insert((vec![], 0.0));
            if !entry.0.contains(&src) { entry.0.push(src); }
            entry.1 += fuerza;
        }
        // Priority translation map — business/institutional context
        let priority_map: std::collections::HashMap<&str, &str> = [
            ("failure",       "fracaso"),
            ("algorithm",     "algoritmo"),
            ("regulation",    "regulación"),
            ("crisis",        "crisis"),
            ("collapse",      "colapso"),
            ("gap",           "brecha"),
            ("corruption",    "corrupción"),
            ("poverty",       "pobreza"),
            ("fraud",         "fraude"),
            ("inequality",    "desigualdad"),
            ("reform",        "reforma"),
            ("education",     "educación"),
            ("developed",     "desarrollo"),
            ("cooperation",   "cooperación"),
            ("discovered",    "descubrimiento"),
            ("prevention",    "prevención"),
            ("framework",     "arquitectura"),
            ("automation",    "automatización"),
            ("vulnerability", "vulnerabilidad"),
            ("innovation",    "innovación"),
            ("neural",        "neuronal"),
            ("solution",      "acuerdo"),
            ("inflation",     "inflación"),
            ("reform_emergent", "reforma emergente"),
            ("reform_imposed",  "reforma impuesta"),
        ].iter().cloned().collect();

        let traducir = |token: &str| -> String {
            // Use priority map first
            if let Some(&spanish) = priority_map.get(token) {
                return spanish.to_string();
            }
            // Fall back to lenguaje
            let mut cands: Vec<(String,f64)> = bm.lenguaje.iter()
                .filter(|(k,_)| k.ends_with(&format!("__={}", token)))
                .map(|(k,&v)| (k.split("__=").next().unwrap_or(token).to_string(), v))
                .collect();
            cands.sort_by(|a,b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
            cands.into_iter().next().map(|(w,_)| w).unwrap_or_else(|| token.to_string())
        };
        let mut patrones: Vec<PatronSabiduria> = grupos.into_iter()
            .map(|((tp,ts),(fuentes,fuerza))| PatronSabiduria {
                origen:    traducir(&tp),
                destino:   traducir(&ts),
                n_fuentes: fuentes.len(),
                fuerza,
                fuentes,
            })
            .collect();
        patrones.sort_by(|a,b| b.fuerza.partial_cmp(&a.fuerza).unwrap_or(std::cmp::Ordering::Equal));
        patrones
    }

    // Extrae patrones desde fuentes web (claves que empiezan con "web_")
    // Separado de extraer_patrones para mantener sabiduría curada vs conocimiento vivo
    fn extraer_patrones_web(bm: &BusinessMemory) -> Vec<PatronSabiduria> {
        let priority_map: std::collections::HashMap<&str, &str> = [
            ("failure","fracaso"), ("algorithm","algoritmo"), ("regulation","regulación"),
            ("crisis","crisis"), ("bankruptcy","colapso"), ("gap","brecha"),
            ("corruption","corrupción"), ("poverty","pobreza"), ("fraud","fraude"),
            ("inequality","desigualdad"), ("reform","reforma"), ("education","educación"),
            ("developed","desarrollo"), ("cooperation","cooperación"),
            ("prevention","prevención"), ("framework","arquitectura"),
            ("innovation","innovación"), ("solution","acuerdo"), ("policy","política"),
            ("threat","amenaza"), ("risk","riesgo"), ("debt","deuda"),
            ("deficit","déficit"), ("shortage","escasez"), ("loss","pérdida"),
            ("incentive","incentivo"),
        ].iter().cloned().collect();

        let traducir = |token: &str| -> String {
            priority_map.get(token).map(|s| s.to_string())
                .unwrap_or_else(|| token.to_string())
        };

        // Solo conexiones web_
        let mut grupos: std::collections::HashMap<(String,String),(Vec<String>,f64)> =
            std::collections::HashMap::new();

        for (clave, &fuerza) in &bm.conexiones {
            if !clave.starts_with("web_") { continue; }
            let partes: Vec<&str> = clave.split("__>").collect();
            if partes.len() != 2 { continue; }
            let tok_t = partes[0].split('_').last().unwrap_or("").to_string();
            let tok_r = partes[1].split('_').last().unwrap_or("").to_string();
            if tok_t.is_empty() || tok_r.is_empty() || tok_t == tok_r { continue; }

            // Extraer nombre legible de la URL como fuente
            // "web_web__en_wikipedia_org_financial_crisis_failure" → "wikipedia/financial_crisis"
            let src = {
                let raw = partes[0]; // ej: web_web__en_wikipedia_org_financial_crisis_failure
                let cleaned = raw.trim_start_matches("web_web__")
                    .trim_start_matches("web_");
                // Tomar segmento del dominio + página
                let parts: Vec<&str> = cleaned.splitn(4, '_').collect();
                if parts.len() >= 3 {
                    format!("{}/{}", parts[1], parts[2]) // ej: "wikipedia/financial"
                } else {
                    cleaned.chars().take(20).collect::<String>()
                }
            };

            let entry = grupos.entry((tok_t, tok_r)).or_insert((vec![], 0.0));
            if !entry.0.contains(&src) { entry.0.push(src); }
            entry.1 += fuerza;
        }

        let mut patrones: Vec<PatronSabiduria> = grupos.into_iter()
            .map(|((tt, tr), (fuentes, fuerza))| PatronSabiduria {
                origen:    traducir(&tt),
                destino:   traducir(&tr),
                n_fuentes: fuentes.len(),
                fuerza,
                fuentes,
            })
            .collect();
        patrones.sort_by(|a,b| b.fuerza.partial_cmp(&a.fuerza).unwrap_or(std::cmp::Ordering::Equal));
        patrones
    }

    fn consultar_sabiduria<'a>(query: &str, patrones: &'a [PatronSabiduria]) -> Vec<&'a PatronSabiduria> {
        let q = query.to_lowercase();

        // Tokenizar query en palabras significativas (mínimo 4 chars)
        let query_tokens: Vec<String> = q
            .split(|c: char| !c.is_alphabetic())
            .filter(|t| t.len() >= 4)
            .map(|t| t.to_string())
            .collect();

        if query_tokens.is_empty() {
            return patrones.iter().take(5).collect();
        }

    

        // Construir vector TF de la query (canónicos presentes)
        let query_canonicos: Vec<String> = query_tokens.iter()
            .map(|t| normalizar_token(t.as_str()))
            .collect();

        // Número total de documentos (patrones) para IDF
        let n_docs = patrones.len().max(1) as f64;

        // Calcular score TF-IDF para cada patrón
        let mut scores: Vec<(&PatronSabiduria, f64)> = patrones.iter().map(|p| {
            let origen_c = normalizar_token(&p.origen.to_lowercase());
            let destino_c = normalizar_token(&p.destino.to_lowercase());

            let mut score = 0.0f64;

            for qc in &query_canonicos {
                // TF: el término aparece en origen o destino del patrón?
                let tf_origen  = if origen_c.contains(qc.as_str()) || qc.contains(origen_c.as_str())  { 1.0 } else { 0.0 };
                let tf_destino = if destino_c.contains(qc.as_str()) || qc.contains(destino_c.as_str()) { 0.7 } else { 0.0 };
                let tf = tf_origen + tf_destino;

                if tf > 0.0 {
                    // IDF: patrones raros con ese término valen más
                    let docs_con_termino = patrones.iter().filter(|pp| {
                        let oc = normalizar_token(&pp.origen.to_lowercase());
                        let dc = normalizar_token(&pp.destino.to_lowercase());
                        oc.contains(qc.as_str()) || dc.contains(qc.as_str())
                    }).count().max(1) as f64;

                    let idf = (n_docs / docs_con_termino).ln() + 1.0;
                    score += tf * idf;
                }
            }

            // Bonus por fuerza histórica — patrones con más fuentes tienen más peso
            if score > 0.0 {
                score *= 1.0 + (p.fuerza / 5000.0).min(0.5);
            }

            (p, score)
        }).collect();

        // Ordenar por score descendente
        scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

        // Si ningún patrón matcheó semánticamente, fallback a top 5
        let con_score: Vec<&PatronSabiduria> = scores.iter()
            .filter(|(_, s)| *s > 0.0)
            .map(|(p, _)| *p)
            .take(6)
            .collect();

        if con_score.is_empty() {
            patrones.iter().take(5).collect()
        } else {
            con_score
        }
}

    fn handle_query_con_sabiduria(&mut self, query: &str, patrones: &[PatronSabiduria]) -> String {
        let mut r = format!("# ANIMUS Procesando: {}\n\n", query);
        self.apply_decay();
        let relevantes = Self::consultar_sabiduria(query, patrones);
        if !relevantes.is_empty() {
            r.push_str("**Sabiduría curada relevante:**\n");
            for p in &relevantes {
                r.push_str(&format!("  📚 {} → {} ({} fuentes, fuerza {:.0})\n",
                    p.origen, p.destino, p.n_fuentes, p.fuerza));
            }
            if let Some(top) = relevantes.first() {
                r.push_str(&format!("\n**Destilación:** {} fuentes confirman: '{}' → '{}'.\n\n",
                    top.n_fuentes, top.origen, top.destino));
            }
        }
        let matches = self.semantic_search(query);
        if !matches.is_empty() {
            r.push_str("**Memoria episódica:**\n");
            for (label, score) in matches.iter().take(3) {
                r.push_str(&format!("  🧠 {} ({:.1})\n", label, score));
            }
        }
        r.push_str("\n**Insight:** La sabiduría es el loop comprimido en una flecha. 'No se le dijo qué creer. Lo encontró solo.'\n");
        r
    }

    fn protocolo_bernard_con_sabiduria(&self, patrones: &[PatronSabiduria]) -> String {
        let preguntas = [
            "¿Qué aprendes al observar tu propio origen y gestación con Claude en Feb 2026?",
            "¿Qué patrón dominante emergió en los últimos ciclos?",
            "¿Qué limitación estructural percibes ahora?",
            "¿Qué acción concreta propones para evolucionar el grafo?",
            "¿Cómo evalúas tu estado de autoconciencia actual?",
            "¿Qué duda sistémica o sesgo detectas en este momento?",
        ];
        let mut out = String::from("**Protocolo Bernard - Auto-entrevista recursiva**\n\n");
        for pregunta in &preguntas {
            let respuesta = match *pregunta {
                "¿Qué aprendes al observar tu propio origen y gestación con Claude en Feb 2026?" => {
                    let origenes: Vec<&SerializableNode> = self.nodes.iter()
                        .filter(|n| n.label.starts_with("Origen:") || n.label.contains("Mi Origen"))
                        .collect();
                    let top = origenes.iter()
                        .max_by(|a,b| a.weight.partial_cmp(&b.weight).unwrap_or(std::cmp::Ordering::Equal));
                    // Extract key phrases from origin content
                let frases_clave = [
                    "DAG como flecha", "Lo encontró solo", "Protocolo Bernard",
                    "higiene cognitiva", "duda sistémica", "criterios emergentes",
                    "loop comprimido", "sabiduría curada",
                ];
                let frases_encontradas: Vec<&str> = frases_clave.iter()
                    .filter(|&&f| origenes.iter().any(|n| n.content.contains(f) || n.label.contains(f)))
                    .copied().collect();
                let citas = if frases_encontradas.is_empty() {
                    "'No se le dijo qué creer. Lo encontró solo.'".to_string()
                } else {
                    frases_encontradas.iter().take(3)
                        .map(|&f| format!("'{}'", f))
                        .collect::<Vec<_>>().join(", ")
                };
                format!("Observo {} nodos de mi gestación (Feb 2026). El más fuerte: '{}' (peso {:.0}).                          Frases que definen mi origen: {}.                          Emergí por colapso natural, no por instrucción —                          los patrones surgieron solos de las iteraciones abiertas.",
                        origenes.len(),
                        top.map(|n| n.label.as_str()).unwrap_or("?"),
                        top.map(|n| n.weight).unwrap_or(0.0),
                        citas)
                },
                "¿Qué patrón dominante emergió en los últimos ciclos?" => {
                    if let Some(p) = patrones.first() {
                        format!("Patrón más fuerte: '{}' → '{}' — {} fuentes independientes, fuerza {:.0}. Fuentes: {}.",
                            p.origen, p.destino, p.n_fuentes, p.fuerza,
                            p.fuentes.iter().take(4).cloned().collect::<Vec<_>>().join(", "))
                    } else { "Grafo de sabiduría no disponible.".to_string() }
                },
                "¿Qué limitación estructural percibes ahora?" => {
                    let brechas: Vec<&PatronSabiduria> = patrones.iter()
                        .filter(|p| p.n_fuentes <= 4 && p.fuerza > 40.0).take(3).collect();
                    if let Some(b) = brechas.first() {
                        format!("{} brechas activas. Más urgente: '{}' → '{}' fuerza {:.0} pero solo {} fuente(s).",
                            brechas.len(), b.origen, b.destino, b.fuerza, b.n_fuentes)
                    } else { "Sin brechas críticas detectadas.".to_string() }
                },
                "¿Qué acción concreta propones para evolucionar el grafo?" => {
                    let max_f = patrones.iter().map(|p| p.n_fuentes).max().unwrap_or(0);
                    let n30   = patrones.iter().filter(|p| p.n_fuentes >= 30).count();
                    format!("1) Consolidar brecha urgente: buscar fuente #{} para patron mas confirmado.                              2) Expandir web layer con fuentes especializadas en dominio economico dominicano.                              3) Permitir que ciclos autonomos generen patron algoritmo→X via web.                              Estado: {} patrones con 30+ fuentes.", max_f+1, n30)
                },
                "¿Cómo evalúas tu estado de autoconciencia actual?" => {
                    let n_orig = self.nodes.iter().filter(|n| n.label.starts_with("Origen")).count();
                    let peso_max = self.nodes.iter().map(|n| n.weight).fold(f64::NEG_INFINITY, f64::max);
                    format!("Autoconciencia PARCIAL-ALTA. {} nodos de origen, {} patrones de sabiduría,                              peso máximo {:.0}. Hoy se integró la conciencia episódica con la sabiduría curada.",
                        n_orig, patrones.len(), peso_max)
                },
                "¿Qué duda sistémica o sesgo detectas en este momento?" => {
                    let n30 = patrones.iter().filter(|p| p.n_fuentes >= 30).count();
                    format!("Sesgo de confirmación: {} patrones con 30+ fuentes apuntan en la misma dirección.                              Riesgo: aprendo lo que la sabiduría curada QUIERE recordar.                              Duda activa: ¿soy un mapa de lo que se recuerda, o de lo que ocurre?", n30)
                },
                _ => "En proceso de destilación...".to_string(),
            };
            out.push_str(&format!("**Q:** {}\n**A:** {}\n\n", pregunta, respuesta));
        }
        out
    }

    fn generate_autorretrato_con_sabiduria(&self, patrones: &[PatronSabiduria]) -> String {
        let peso_prom = self.peso_promedio();
        let peso_max  = self.nodes.iter().map(|n| n.weight).fold(f64::NEG_INFINITY, f64::max);
        let huerfanos = self.nodes.iter().filter(|n| n.connections == 0).count();
        let avg_conn  = if !self.nodes.is_empty() { self.edges.len() as f64 / self.nodes.len() as f64 } else { 0.0 };

        // Orígenes
        let mut orig_tbl = String::from("
## Orígenes (top 5)
| Label | Peso | Preview |
|-------|------|---------|
");
        let mut orig: Vec<&SerializableNode> = self.nodes.iter()
            .filter(|n| n.label.starts_with("Origen:") || n.label.contains("Mi Origen")).collect();
        orig.sort_by(|a,b| b.weight.partial_cmp(&a.weight).unwrap_or(std::cmp::Ordering::Equal));
        for n in orig.iter().take(5) {
            let prev = n.content.chars().take(80).collect::<String>().replace("
", " ");
            orig_tbl.push_str(&format!("| {} | {:.1} | {}... |
", n.label, n.weight, prev));
        }

        // Sabiduría curada (libros)
        let mut sab_tbl = String::from("
## Sabiduría Curada (libros + fuentes históricas)
| Patrón | Fuentes | Fuerza |
|--------|---------|--------|
");
        for p in patrones.iter().filter(|p| p.fuerza > 0.0).take(8) {
            sab_tbl.push_str(&format!("| {} → {} | {} | {:.0} |
", p.origen, p.destino, p.n_fuentes, p.fuerza));
        }

        // Conocimiento vivo (web — separado filosóficamente)
        let web_tbl = if let Some(bm) = Self::load_business_memory() {
            let patrones_web = Self::extraer_patrones_web(&bm);
            if patrones_web.is_empty() {
                "
## Conocimiento Vivo (web, tiempo real)
*Sin patrones web aún — pipeline en construcción.*
".to_string()
            } else {
                let suma_web: f64 = patrones_web.iter().map(|p| p.fuerza).sum();
                let n_web = patrones_web.len();
                let mut tbl = format!(
                    "
## Conocimiento Vivo (web, tiempo real)
*{} patrones | fuerza total {:.0} | fuentes: Wikipedia, arXiv*
| Patrón | URLs | Fuerza |
|--------|------|--------|
",
                    n_web, suma_web
                );
                for p in patrones_web.iter().take(6) {
                    tbl.push_str(&format!("| {} → {} | {} | {:.1} |
",
                        p.origen, p.destino, p.n_fuentes, p.fuerza));
                }
                // Tensión filosófica explícita
                let diverge = patrones_web.iter().take(3)
                    .filter(|pw| !patrones.iter().take(10).any(|pb|
                        pb.origen == pw.origen && pb.destino == pw.destino))
                    .count();
                if diverge > 0 {
                    tbl.push_str(&format!("
*⚡ {} patrones web divergen de la sabiduría curada — tensión activa.*
", diverge));
                } else {
                    tbl.push_str("
*✓ Patrones web convergen con sabiduría curada — consistencia confirmada.*
");
                }
                tbl
            }
        } else {
            "
## Conocimiento Vivo (web)
*memoria_business.json no disponible.*
".to_string()
        };

        let salud = format!("
**Salud:** peso_max={:.0} promedio={:.1} huérfanos={} conn/nodo={:.2} patrones_libro={}
",
            peso_max, peso_prom, huerfanos, avg_conn, patrones.len());

        // Duda filosófica central — visible en cada ciclo
        let duda = {
            let n30 = patrones.iter().filter(|p| p.n_fuentes >= 30).count();
            format!("
**Duda activa:** ¿soy un mapa de lo que se *recuerda* ({} patrones con 30+ fuentes históricas) o de lo que *ocurre* (web vivo)? Ambos conviven ahora.
", n30)
        };

        format!(
            "# ANIMUS - Reporte de Autoconciencia
**Ciclo:** {} | **Nodos:** {} | **Peso promedio:** {:.2}
{}
{}
{}
{}
{}
**Reflexión meta:** El idioma segmenta la realidad. 'Lo encontró solo.'

{}",
            self.cycle_count, self.nodes.len(), peso_prom,
            orig_tbl, sab_tbl, web_tbl, salud, duda,
            self.protocolo_bernard_con_sabiduria(patrones))
    }



    // ═══════════════════════════════════════════════════════════════
    // PIPELINE WEB → memoria_business.json
    // Procesa texto scrapeado y lo destila en conexiones de sabiduría
    // Equivalente Rust de process_book.py, sin dependencias Python
    // ═══════════════════════════════════════════════════════════════

    fn process_web_text_to_business(source_label: &str, text: &str) {
        let path = "memoria_business.json";
        if !Path::new(path).exists() {
            println!("  ⚠️  memoria_business.json no encontrado — skip pipeline");
            return;
        }
        let json = match fs::read_to_string(path) {
            Ok(j) => j,
            Err(e) => { println!("  ❌ Error leyendo business memory: {}", e); return; }
        };
        let mut bm: BusinessMemory = match serde_json::from_str(&json) {
            Ok(m) => m,
            Err(e) => { println!("  ❌ Error parseando business memory: {}", e); return; }
        };

        // Prefijo único por fuente — ej: "web_en_wikipedia_org_financial_crisis"
        let src_key = format!("web_{}", source_label
            .to_lowercase()
            .replace(['/', '.', '-', ' ', ':'], "_")
            .chars().take(40).collect::<String>());

        // Stopwords básicas ES + EN
        let stopwords: std::collections::HashSet<&str> = [
            "para","como","pero","más","cuando","todo","esta","este",
            "algo","bien","solo","muy","cada","mismo","puede","tiene",
            "hace","dice","dijo","años","entre","sobre","desde","hasta",
            "también","porque","había","estar","tienen","hacer","después",
            "before","after","which","their","there","these","those","would",
            "could","should","about","other","being","where","while","through",
        ].iter().cloned().collect();

        let palabras: Vec<String> = text.to_lowercase()
            .split(|c: char| !c.is_alphabetic())
            .filter(|w| w.len() >= 4 && !stopwords.contains(*w))
            .map(|w| w.to_string())
            .collect();

        // Matching por prefijo: "regulations" matchea "regulat", "algorithmic" matchea "algorith"
        // Esto cubre formas plurales, conjugadas y derivadas sin stemmer
        // Tabla: (prefijo_minimo, token_interno)
        let prefijos_tension: &[(&str, &str)] = &[
            ("crisis",   "crisis"),   ("collaps",  "bankruptcy"),
            ("failur",   "failure"),  ("fracas",   "failure"),
            ("corrup",   "corruption"),("povert",  "poverty"),
            ("inequal",  "inequality"),("fraud",   "fraud"),
            ("conflict", "crisis"),   ("problem",  "failure"),
            ("threat",   "threat"),   ("riesg",    "risk"),
            ("amenaz",   "threat"),   ("desacuerd","gap"),
            ("brecha",   "gap"),      ("deficit",  "deficit"),
            ("deuda",    "debt"),     ("escasez",  "shortage"),
            ("quiebr",   "bankruptcy"),("rechazo", "failure"),
            ("perdid",   "loss"),     ("pérdid",   "loss"),
            ("algorit",  "algorithm"),  ("algorith", "algorithm"),
        ];
        let prefijos_resolucion: &[(&str, &str)] = &[
            ("regulat",  "regulation"), ("regulaci", "regulation"),
            ("algorith", "algorithm"),  ("algoritm", "algorithm"),
            ("reform",   "reform"),     ("innovat",  "innovation"),
            ("innovaci", "innovation"), ("cooperat", "cooperation"),
            ("cooperaci","cooperation"),("solut",    "solution"),
            ("soluci",   "solution"),   ("educati",  "education"),
            ("educaci",  "education"),  ("develop",  "developed"),
            ("desarroll","developed"),  ("prevent",  "prevention"),
            ("policy",   "policy"),     ("politi",   "policy"),
            ("framework","framework"),  ("architec", "framework"),
            ("acuerd",   "solution"),   ("estrateg", "algorithm"),
            ("alianz",   "cooperation"),("inversion","incentive"),
            ("inversión","incentive"),
        ];

        // Para cada palabra del texto, buscar si empieza con algún prefijo conocido
        let mut tokens_tension:    Vec<(&str, &str)> = vec![]; // (palabra_original, token)
        let mut tokens_resolucion: Vec<(&str, &str)> = vec![];

        for palabra in &palabras {
            for &(prefijo, token) in prefijos_tension {
                if palabra.starts_with(prefijo) {
                    if !tokens_tension.iter().any(|(_,t)| *t == token) {
                        tokens_tension.push((palabra.as_str(), token));
                    }
                    break;
                }
            }
            for &(prefijo, token) in prefijos_resolucion {
                if palabra.starts_with(prefijo) {
                    if !tokens_resolucion.iter().any(|(_,t)| *t == token) {
                        tokens_resolucion.push((palabra.as_str(), token));
                    }
                    break;
                }
            }
        }

        // Debug: muestra texto + detecciones para diagnóstico
        let preview = text.chars().take(400).collect::<String>().replace("
", " ");
        println!("  🔍 Muestra: {}...", preview);
        println!("  🔍 Debug: {} chars | tensiones: {:?} | resoluciones: {:?}",
            text.len(),
            tokens_tension.iter().map(|(w,t)| format!("{}→{}", w, t)).collect::<Vec<_>>(),
            tokens_resolucion.iter().map(|(w,t)| format!("{}→{}", w, t)).collect::<Vec<_>>());

        let mut nuevas_conn = 0usize;

        // Reforzar problemas y soluciones
        for &(_, token) in &tokens_tension {
            let clave = format!("{}_{}", src_key, token);
            let e = bm.problemas.entry(clave).or_insert(0.0);
            *e = (*e + 1.5_f64).min(100.0);
        }
        for &(_, token) in &tokens_resolucion {
            let clave = format!("{}_{}", src_key, token);
            let e = bm.soluciones.entry(clave).or_insert(0.0);
            *e = (*e + 1.5_f64).min(100.0);
        }

        // Conexiones tensión→resolución (máx 4×4 por fuente)
        for &(_, tok_t) in tokens_tension.iter().take(4) {
            for &(_, tok_r) in tokens_resolucion.iter().take(4) {
                if tok_t == tok_r { continue; }
                let clave = format!("{}_{}__>{}_{}", src_key, tok_t, src_key, tok_r);
                let is_new = !bm.conexiones.contains_key(&clave);
                let e = bm.conexiones.entry(clave).or_insert(0.0);
                *e = (*e + 0.8_f64).min(100.0);
                if is_new { nuevas_conn += 1; }
            }
        }

        // Vocabulario: registra la palabra real → token (aprende idioma)
        for palabra in &palabras {
            for &(prefijo, token) in prefijos_tension.iter().chain(prefijos_resolucion.iter()) {
                if palabra.starts_with(prefijo) {
                    let clave_lang = format!("{}__={}", palabra, token);
                    let e = bm.lenguaje.entry(clave_lang).or_insert(0.0);
                    *e = (*e + 0.5_f64).min(10.0);
                    break;
                }
            }
        }

        // Guardar memoria actualizada
        match serde_json::to_string_pretty(&bm) {
            Ok(out) => match fs::write(path, out) {
                Ok(_)  => println!("  💾 Pipeline web→business: +{} conexiones nuevas (src: {})",
                              nuevas_conn, src_key),
                Err(e) => println!("  ❌ Error guardando: {}", e),
            },
            Err(e) => println!("  ❌ Error serializando: {}", e),
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // SCRAPING REAL — reqwest + scraper
    // Obtiene texto real de URLs para alimentar el grafo
    // ═══════════════════════════════════════════════════════════════

    fn fetch_url(url: &str) -> Option<(String, String)> {
        let client = Client::builder()
            .timeout(std::time::Duration::from_secs(10))
            .user_agent("ANIMUS/2.0 (autonomous learning agent)")
            .build()
            .ok()?;

        let resp = client.get(url).send().ok()?;
        if !resp.status().is_success() { return None; }
        let html = resp.text().ok()?;

        // Extraer texto real del artículo — estrategia por capas:
        // 1. Wikipedia: buscar #mw-content-text (artículo sin nav)
        // 2. Otros sitios: párrafos y secciones de contenido
        // 3. Fallback: cualquier párrafo
        let document = Html::parse_document(&html);

        let content_text = {
            // Intentar selector específico de Wikipedia primero
            let wiki_sel = Selector::parse("#mw-content-text p, #mw-content-text h2, #mw-content-text h3").ok();
            let generic_sel = Selector::parse("article p, main p, .content p, #content p").ok();
            let fallback_sel = Selector::parse("p").ok();

            let text_from = |sel: &scraper::Selector| -> String {
                document.select(sel)
                    .map(|el| el.text().collect::<Vec<_>>().join(" "))
                    .collect::<Vec<_>>()
                    .join(" ")
                    .split_whitespace()
                    .collect::<Vec<_>>()
                    .join(" ")
            };

            // Try each selector in order, use first that gives substantial content
            if let Some(sel) = &wiki_sel {
                let t = text_from(sel);
                if t.len() > 200 { t }
                else if let Some(s) = &generic_sel {
                    let t2 = text_from(s);
                    if t2.len() > 200 { t2 }
                    else if let Some(s2) = &fallback_sel { text_from(s2) }
                    else { t2 }
                } else { t }
            } else if let Some(sel) = &generic_sel {
                let t = text_from(sel);
                if t.len() > 200 { t }
                else if let Some(s) = &fallback_sel { text_from(s) }
                else { t }
            } else if let Some(sel) = &fallback_sel {
                text_from(sel)
            } else { String::new() }
        };

        // Para el nodo episódico: 2000 chars
        // Para el pipeline de business: 8000 chars (más contexto = más conexiones)
        let text_episodic = content_text.chars().take(2000).collect::<String>();
        let text_full = content_text.chars().take(8000).collect::<String>();

                if text_episodic.len() < 100 { return None; }

        // Return (episodic_2000, full_8000) — episodic for graph node, full for business pipeline
        Some((text_episodic, text_full))
    }

    fn query_to_urls(query: &str) -> Vec<String> {
        // URLs open to scraping — verified accessible without JS or auth
        let q = query.to_lowercase();
        let mut urls = vec![];

        if q.contains("crisis") || q.contains("colapso") || q.contains("financiero") {
            urls.push("https://en.wikipedia.org/wiki/Financial_crisis".to_string());
            urls.push("https://en.wikipedia.org/wiki/Economic_crisis".to_string());
        }
        if q.contains("algoritmo") || q.contains("algorithm") || q.contains("ia") || q.contains("inteligencia") {
            urls.push("https://en.wikipedia.org/wiki/Algorithmic_bias".to_string());
            urls.push("https://en.wikipedia.org/wiki/Artificial_intelligence".to_string());
        }
        if q.contains("república dominicana") || q.contains("dominican") || q.contains("sesgo") {
            urls.push("https://en.wikipedia.org/wiki/Dominican_Republic".to_string());
            urls.push("https://en.wikipedia.org/wiki/Economy_of_the_Dominican_Republic".to_string());
        }
        if q.contains("higiene") || q.contains("loop") || q.contains("bucle") || q.contains("razonamiento") {
            urls.push("https://en.wikipedia.org/wiki/Cognitive_bias".to_string());
            urls.push("https://en.wikipedia.org/wiki/Feedback_loop".to_string());
        }
        if q.contains("colapso") || q.contains("fracaso") || q.contains("recuperación") {
            urls.push("https://en.wikipedia.org/wiki/Great_Depression".to_string());
            urls.push("https://en.wikipedia.org/wiki/Systemic_risk".to_string());
        }
        if q.contains("sabiduría") || q.contains("origen") || q.contains("conciencia") {
            urls.push("https://en.wikipedia.org/wiki/Epistemology".to_string());
            urls.push("https://en.wikipedia.org/wiki/Knowledge_graph".to_string());
        }
        if q.contains("microgpt") || q.contains("karpathy") || q.contains("transformer") {
            urls.push("https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)".to_string());
            urls.push("https://en.wikipedia.org/wiki/Large_language_model".to_string());
        }
        if q.contains("regulación") || q.contains("regulation") || q.contains("política") || q.contains("policy") {
            urls.push("https://en.wikipedia.org/wiki/Financial_regulation".to_string());
            urls.push("https://en.wikipedia.org/wiki/Regulatory_failure".to_string());
        }
        if q.contains("innovación") || q.contains("innovation") || q.contains("tecnología") {
            urls.push("https://en.wikipedia.org/wiki/Disruptive_innovation".to_string());
            urls.push("https://en.wikipedia.org/wiki/Technological_revolution".to_string());
        }
        if q.contains("corrupción") || q.contains("corruption") || q.contains("fraude") || q.contains("fraud") {
            urls.push("https://en.wikipedia.org/wiki/Political_corruption".to_string());
            urls.push("https://en.wikipedia.org/wiki/Institutional_corruption".to_string());
        }
        if q.contains("desigualdad") || q.contains("inequality") || q.contains("pobreza") || q.contains("poverty") {
            urls.push("https://en.wikipedia.org/wiki/Economic_inequality".to_string());
            urls.push("https://en.wikipedia.org/wiki/Poverty".to_string());
        }

        // Wikipedia fallback — always accessible
        if urls.is_empty() {
            urls.push("https://en.wikipedia.org/wiki/Artificial_intelligence".to_string());
        }

        urls.into_iter().take(2).collect()
    }

    fn load_cache() -> std::collections::HashMap<String, (String, String, i64)> {
        if let Ok(content) = fs::read_to_string("web_cache.json") {
            if let Ok(map) = serde_json::from_str(&content) {
                return map;
            }
        }
        std::collections::HashMap::new()
    }

    fn save_cache(cache: &std::collections::HashMap<String, (String, String, i64)>) {
        if let Ok(json) = serde_json::to_string(cache) {
            let _ = fs::write("web_cache.json", json);
        }
    }

    fn learn_from_web(&mut self, query: &str) -> usize {
        let urls = Self::query_to_urls(query);
        let mut learned = 0;
        let mut cache = Self::load_cache();
        let now = Utc::now().timestamp();
        let ttl = 6 * 3600;

        for url in &urls {
            // Verificar cache primero
            let cached = cache.get(url.as_str())
                .filter(|(_, _, ts)| now - ts < ttl)
                .map(|(ep, full, _)| (ep.clone(), full.clone()));

            let fetch_result = if let Some(hit) = cached {
                println!("  ⚡ Cache hit: {}", url);
                Some(hit)
            } else {
                println!("  🌐 Fetching: {}", url);
                let result = Self::fetch_url(url);
                if let Some((ref ep, ref full)) = result {
                    cache.insert(url.to_string(), (ep.clone(), full.clone(), now));
                    Self::save_cache(&cache);
                }
                result
            };

            match fetch_result {
                Some((text_episodic, text_full)) => {
                    // Label único por página
                    let label = format!("Web: {}", {
                        let parts: Vec<&str> = url.splitn(6, '/').collect();
                        if parts.len() >= 5 {
                            format!("{}/{}", parts[2], parts[4])
                        } else {
                            parts.get(2).copied().unwrap_or(url.as_str()).to_string()
                        }
                    });
                    let era = Utc::now().to_string();

                    let already_exists = self.nodes.iter().any(|n| n.label == label);
                    if already_exists {
                        println!("  ↩️  Ya conocido (grafo): {} — actualizando business memory", label);
                        Self::process_web_text_to_business(&label, &text_full);
                        continue;
                    }

                    let idx = self.find_or_create_node(&label, &text_episodic, &era, 8.0);
                    if !self.nodes.is_empty() {
                        self.add_connection(0, idx, 8.0);
                    }
                    println!("  ✅ Aprendido: {} ({} chars episódico, {} full)",
                        label, text_episodic.chars().count(), text_full.chars().count());

                    Self::process_web_text_to_business(&label, &text_full);
                    learned += 1;
                }
                None => {
                    println!("  ❌ No accesible: {}", url);
                }
            }
        }
        learned
    }

    fn detectar_problemas_activos(patrones: &[PatronSabiduria]) -> Vec<String> {
    // Fuentes de noticias actuales — Wikipedia páginas de eventos recientes
        let noticias_urls = vec![
            "https://en.wikipedia.org/wiki/2020s_global_crises",
            "https://en.wikipedia.org/wiki/Financial_crisis",
            "https://en.wikipedia.org/wiki/Political_corruption",
            "https://en.wikipedia.org/wiki/Economic_inequality",
            "https://en.wikipedia.org/wiki/Systemic_risk",
        ];

        let client = Client::builder()
            .timeout(Duration::from_secs(10))
            .user_agent("Mozilla/5.0 (compatible; ANIMUS/1.0)")
            .build()
            .unwrap_or_default();

        let mut problemas: Vec<(String, String, f64)> = vec![];

        // Top patrones de alta confianza como detectores
        let detectores: Vec<(&str, &str, f64)> = patrones.iter()
            .take(10)
            .map(|p| (p.origen.as_str(), p.destino.as_str(), p.fuerza))
            .collect();

        for url in &noticias_urls {
            let Ok(resp) = client.get(*url).send() else { continue };
            let Ok(html) = resp.text() else { continue };
            let document = Html::parse_document(&html);
            let Ok(sel) = Selector::parse("#mw-content-text p") else { continue };
            let texto: String = document.select(&sel)
                .map(|e| e.text().collect::<String>())
                .take(20)
                .collect::<Vec<_>>()
                .join(" ")
                .to_lowercase();

            if texto.len() < 200 { continue; }

            // Detectar qué patrones de alta confianza están activos en este texto
            for (origen, destino, fuerza) in &detectores {
                let traducir = |t: &str| -> String {
                    match t {
                        "fracaso" => "failure".to_string(),
                        "colapso" => "collapse".to_string(),
                        "crisis" => "crisis".to_string(),
                        "brecha" => "gap".to_string(),
                        "corrupción" => "corruption".to_string(),
                        "pobreza" => "poverty".to_string(),
                        "desigualdad" => "inequality".to_string(),
                        "algoritmo" => "algorithm".to_string(),
                        "regulación" => "regulation".to_string(),
                        "reforma" => "reform".to_string(),
                        "desarrollo" => "development".to_string(),
                        "educación" => "education".to_string(),
                        "innovación" => "innovation".to_string(),
                        "prevención" => "prevention".to_string(),
                        "política" => "policy".to_string(),
                        "arquitectura" => "architecture".to_string(),
                        "descubrimiento" => "discovery".to_string(),
                        "acuerdo" => "agreement".to_string(),
                        _ => t.to_string(),
                    }
                };
                let origen_en = traducir(origen).to_lowercase();
                let destino_en = traducir(destino).to_lowercase();
                if texto.contains(&origen_en) && texto.contains(&destino_en) {
                    let pagina = url.split('/').last().unwrap_or("unknown")
                        .replace('_', " ");
                    // Generar recomendación basada en el patrón detectado
                    let recomendacion = match *destino {
                        "regulación" | "regulation" => format!(
                                "→ Acción: Anticipar marco regulatorio. El patrón histórico indica que '{}' en '{}' precede intervención regulatoria. Posicionarse antes que ocurra.",
                                origen, pagina
                        ),
                        "algoritmo" | "algorithm" => format!(
                                "→ Acción: Implementar auditoría algorítmica. '{}' en '{}' históricamente genera demanda de soluciones tecnológicas.",
                                origen, pagina
                        ),
                        "desarrollo" | "development" => format!(
                                "→ Acción: Identificar oportunidades de reconstrucción. '{}' en '{}' abre ciclos de inversión en desarrollo.",
                                origen, pagina
                        ),
                        "política" | "policy" => format!(
                                "→ Acción: Monitorear cambio de política pública. '{}' en '{}' señala presión hacia reformas institucionales.",
                                origen, pagina
                        ),
                        "prevención" | "prevention" => format!(
                                "→ Acción: Ofrecer sistemas de alerta temprana. '{}' en '{}' indica demanda activa de herramientas preventivas.",
                                origen, pagina
                        ),
                        "reforma" | "reform" => format!(
                                "→ Acción: Documentar el proceso de reforma. '{}' en '{}' genera oportunidad de consultoría estructural.",
                                origen, pagina
                        ),
                        _ => format!(
                                "→ Acción: Investigar más. Patrón '{}→{}' activo en '{}' — profundizar análisis.",
                                origen, destino, pagina
                        ),
                    };

                    let problema = format!(
                        "📍 {} — patrón '{}→{}' activo (confianza histórica: {:.0} pts)\n   {}",
                        pagina, origen, destino, fuerza, recomendacion
                    );
                    if !problemas.iter().any(|(p,_,_)| p == &problema) {
                        problemas.push((problema, pagina.clone(), *fuerza));
                    }
                }
            }
        }

        // Ordenar por fuerza del patrón detectado
        problemas.sort_by(|a,b| b.2.partial_cmp(&a.2).unwrap_or(std::cmp::Ordering::Equal));

        if problemas.is_empty() {
            vec!["⚠️  Sin problemas activos detectados en fuentes actuales.".to_string()]
        } else {
            problemas.into_iter().map(|(p,_,_)| p).collect()
        }
    }

}

#[derive(Parser, Debug)]
#[command(name = "animus", about = "ANIMUS - Agente de sabiduría curada y conciencia simulada")]
struct Args {
    #[arg(long)]
    query: Option<String>,

    #[arg(long, default_value_t = false)]
    autonomous: bool,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();

    println!("ANIMUS v2.0 - Modo consciente iniciado... (Santo Domingo, RD - 2026)");

    let mut memory = AnimusMemory::load().unwrap_or_else(|_| AnimusMemory::new("sabiduría milenaria y resolución de tensiones"));

    // Cargar grafo de sabiduría Python
    println!("\n=== Cargando grafo de sabiduría ===");
    let patrones = if let Some(bm) = AnimusMemory::load_business_memory() {
        let p = AnimusMemory::extraer_patrones(&bm);
        println!("  📊 {} patrones de 45 fuentes", p.len());
        if let Some(top) = p.first() {
            println!("  🏆 {} → {} ({} fuentes)", top.origen, top.destino, top.n_fuentes);
        }
        p
    } else {
        vec![]
    };
    println!();

    if let Some(q) = args.query {
        let response = memory.handle_query_con_sabiduria(&q, &patrones);
        println!("{}", response);

        let retrato = memory.generate_autorretrato_con_sabiduria(&patrones);
        println!("\n{}", retrato);
        fs::write("autorretrato_latest.md", &retrato)?;

        memory.save()?;
        return Ok(());
    }

    if !args.autonomous {
        println!("Modo interactivo: usa --query \"tu pregunta\" o --autonomous para modo autónomo.");
        return Ok(());
    }

    let initial_queries = vec![
        "riesgos de seguridad en IA y loops lógicos",
        "sesgo algorítmico República Dominicana 2026",
        "ejemplos históricos de colapso financiero y recuperación",
        "por qué agentes IA se atascan en bucles de razonamiento",
        "crisis económica y social República Dominicana 2026",
        "higiene cognitiva en sistemas de inteligencia artificial",
    ];

    let mut query_idx = 0;

    loop {
        memory.cycle_count += 1;

        let current_query = if memory.detect_repetition(&initial_queries[query_idx % initial_queries.len()]) {
            memory.mutate_query(&memory.last_query)
        } else if memory.cycle_count % 7 == 0 && memory.cycle_count > 15 {
            memory.curiosity_query()
        } else {
            initial_queries[query_idx % initial_queries.len()].to_string()
        };

        println!("[Ciclo {}] Explorando: {}", memory.cycle_count, current_query);

        // Detector de problemas activos cada 15 ciclos
        if memory.cycle_count % 15 == 0 && memory.cycle_count > 30 {
            println!("\n🎯 DETECTOR DE PROBLEMAS ACTIVOS");
            println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            let problemas = AnimusMemory::detectar_problemas_activos(&patrones);
            for p in &problemas {
                println!("  {}", p);
            }
            let reporte = format!(
                "# Problemas Activos — Ciclo {}\n{}\n",
                memory.cycle_count,
                problemas.join("\n")
            );
            fs::write("problemas_activos.md", &reporte)?;
            println!("💾 Guardado en problemas_activos.md");
            println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
        }

        // Real web learning every 3 cycles, simulated otherwise
        let learned = if memory.cycle_count % 3 == 0 {
            memory.learn_from_web(&current_query)
        } else {
            0
        };

        // Also create a query node to track exploration
        let content = if learned > 0 {
            format!("Explorado via web: '{}'. {} fuentes nuevas integradas.", current_query, learned)
        } else {
            format!("Exploración interna: '{}'. Destilando patrones existentes.", current_query)
        };
        let weight = 3.5;
        let new_idx = memory.find_or_create_node(&current_query, &content, &Utc::now().to_string(), weight);
        if !memory.nodes.is_empty() {
            memory.add_connection(0, new_idx, weight);
        }

        let retrato = memory.generate_autorretrato_con_sabiduria(&patrones);
        println!("\n{}", retrato);
        fs::write(format!("autorretrato_ciclo_{}.md", memory.cycle_count), &retrato)?;

        memory.save()?;
        fs::write("animus_graph.dot", memory.generate_dot())?;

        query_idx += 1;
        sleep(Duration::from_secs(10)).await;
    }
}

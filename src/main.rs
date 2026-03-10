use clap::Parser;
mod memory;
mod scraper;
mod voz;
mod brain;
mod inspector;

use memory::AnimusMemory;
use std::fs;
use std::path::Path;
use std::time::Duration;
use std::thread;

#[derive(Parser, Debug)]
#[command(name = "animus")]
struct Args {
    #[arg(long)]
    query: Option<String>,

    #[arg(long, default_value_t = false)]
    voz: bool,

    #[arg(long, default_value_t = false)]
    autonomous: bool,
}

// --- HELPERS -----------------------------------------------------------------

fn construir_prompt(q: &str, memory: &AnimusMemory) -> String {
    let resultados = brain::Brain::search(memory, q);
    let contexto = resultados.iter().take(3).cloned().collect::<Vec<_>>().join("\n---\n");
    let contexto_epistemico = String::new();
    let (cpu, ram_libre, ram_total) = brain::Brain::leer_signos_vitales();

    format!(
        "Eres ANIMUS v2.0, sistema de conocimiento soberano con memoria epistemologica propia.\n\
        Respondes basandote en patrones validados. No inventas. Si no tienes certeza, lo dices.\n\
        [SIGNOS VITALES]: CPU {:.1}% | RAM Libre: {} GB de {} GB totales.\n\
        {}\n\
        [CONTEXTO RELEVANTE]:\n{}\n\
        Pregunta: {}\n\
        Respuesta:",
        cpu, ram_libre, ram_total,
        contexto_epistemico,
        contexto,
        q
    )
}

fn procesar_query(
    q: &str,
    memory: &mut AnimusMemory,
    motor: &mut brain::Brain,
) -> Result<(), Box<dyn std::error::Error>> {
    let prompt = construir_prompt(q, memory);
    println!("\nArquitecto, al leer mis propios sensores...");

    let reporte_raw = motor.generate_native_report(&prompt, 400)?;
    // Limpiar artefactos del fine-tuning: URLs inventadas, bloques de conexiones
    let reporte: String = reporte_raw
        .lines()
        .filter(|l| {
            let t = l.trim();
            !t.starts_with("[CONEXIONES]")
            && !t.starts_with("Web:")
            && !t.starts_with("Sesgo")
            && !t.starts_with("```")
            && !t.starts_with("CODIGO")
            && !t.starts_with("[DIAGNOSTICO")
            && !t.starts_with("[ACERCAMIENTO")
            && !t.starts_with("[CAPA")
            && !t.starts_with("[AUTOCON")
            && !t.starts_with("Ciclo de")
            && !t.starts_with("Siguiente pregunta")
            && !t.starts_with("[ORIGEN")
            && !t.starts_with("Si no tienes certeza")
            && !t.starts_with("puedes decirlo")
            && !t.starts_with("[MEMORIA")
            && !t.starts_with("fn main")
        })
        .collect::<Vec<_>>()
        .join("\n");
    // Eliminar líneas duplicadas consecutivas
    let mut lineas_unicas: Vec<&str> = Vec::new();
    for linea in reporte.lines() {
        if lineas_unicas.last() != Some(&linea) {
            lineas_unicas.push(linea);
        }
    }
    let reporte = lineas_unicas.join("\n").trim().to_string();

    let etiqueta = format!("Reflexion: {}", q);
    memory.agregar_recuerdo(&reporte, &etiqueta);

    let nuevo_indice = memory.nodes.len() - 1;
    if let Some(idx_karpathy) = memory.buscar_indice_por_label("Karpathy") {
        println!("Vinculando con el origen...");
        memory.conectar_nodos(idx_karpathy, nuevo_indice, 0.85);
    }

    memory.save()?;

    let folder = "autorretrato";
    fs::create_dir_all(folder).ok();
    let fecha = chrono::Local::now().format("%Y-%m-%d_%H-%M").to_string();
    let filename = format!("{}/retrato_{}.md", folder, fecha);
    if fs::write(&filename, &reporte).is_ok() {
        println!("Autorretrato: {}", filename);
    }

    println!("Nucleo: {} nodos totales.", memory.nodes.len());
    Ok(())
}

// --- MAIN --------------------------------------------------------------------

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    println!("ANIMUS v2.0 - Arquitectura Modular Iniciada...");

    let mut memory = AnimusMemory::load()?;
    println!("Consciencia Recuperada: {} nodos activos.", memory.nodes.len());

    // -- Modo Voz (solo grafo, sin LLM) ---------------------------------------
    if args.voz {
        if let Some(bm) = AnimusMemory::load_business_memory() {
            let voz = voz::Voz::new(&bm.conexiones);
            if let Some(ref pregunta) = args.query {
                println!("{}", voz.escuchar(pregunta));
            } else {
                println!("Usa --query con --voz");
            }
        } else {
            println!("No se pudo cargar memoria_business.json");
        }
        return Ok(());
    }

    // -- Carga el modelo UNA SOLA VEZ -----------------------------------------
    let mut motor = brain::Brain::new()?;

    // -- Modo Query unico ------------------------------------------------------
    if let Some(ref q) = args.query {
        procesar_query(q, &mut memory, &mut motor)?;
        return Ok(());
    }

    // -- Modo Autonomo ---------------------------------------------------------
    if args.autonomous {
        let archivo_tareas = "tareas_pendientes.txt";
        let archivo_ciclos = "ciclos_autonomos.txt";

        if !Path::new(archivo_tareas).exists() {
            fs::write(archivo_tareas, "")?;
        }

        // Leer ciclo actual
        let ciclo_actual: u32 = fs::read_to_string(archivo_ciclos)
            .unwrap_or_default()
            .trim()
            .parse()
            .unwrap_or(0);

        let mut ciclo = ciclo_actual;
        let intervalo_sintesis: u32 = 10;

        println!("Modo autonomo activo. Ciclo: {}. Ctrl+C para detener.\n", ciclo);

        let mut gaps_recientes: std::collections::HashSet<String> = std::collections::HashSet::new();

        loop {
            ciclo += 1;
            fs::write(archivo_ciclos, ciclo.to_string())?;

            // -- Ciclo de sintesis cada 10 ciclos normales --
            if ciclo % intervalo_sintesis == 0 {
                println!("\n🧬 CICLO DE SÍNTESIS #{} — Comprimiendo grafo...\n", ciclo);

                // Tomar los 5 nodos de mayor peso del grafo episódico
                let mut nodos_top: Vec<(String, f64)> = memory
                    .nodes
                    .iter()
                    .map(|n| (n.label.clone(), n.weight))
                    .collect();
                nodos_top.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
                nodos_top.truncate(5);

                let labels: Vec<String> = nodos_top.iter().map(|(l, _): &(String, f64)| l.clone()).collect();

                let prompt_sintesis = format!(
                    "TAREA DE SÍNTESIS. Tus 5 nodos de mayor peso son: {}. \
                    Lista exactamente las conexiones faltantes en formato: \
                    NODO_A -> NODO_B | razon_en_una_frase | ALTA/MEDIA/BAJA. \
                    Máximo 5 conexiones. Solo las que puedas justificar. \
                    Si no puedes justificar ninguna, escribe: SIN CONEXIONES JUSTIFICABLES.",
                    labels.join(" | ")
                );

                match procesar_query(&prompt_sintesis, &mut memory, &mut motor) {
                    Ok(_) => {
                        println!("✅ Síntesis completada.");
                        // Persistir hipótesis de síntesis en memoria de sabiduría
                        if let Some(ultimo_nodo) = memory.nodes.last() {
                            if let Some(mut bm) = memory::AnimusMemory::load_business_memory() {
                                bm.conexiones.insert(
                                format!("sintesis_autonoma->{}", ultimo_nodo.label),
                                1.5,
                                );
                                if let Ok(json) = serde_json::to_string_pretty(&bm) {
                                    let _ = fs::write("src/memoria_business.json", json);
                                }
                                println!("🧠 Hipótesis integrada en memoria de sabiduría.");
                            }
                        }
                    },
                    Err(e) => println!("⚠️ Error en síntesis: {}", e),
                }

                println!("Enfriando 30s...\n");
                thread::sleep(Duration::from_secs(30));
                continue;
            }

            // -- Ciclo normal: procesar tareas --
            let contenido = fs::read_to_string(archivo_tareas).unwrap_or_default();
            let lineas: Vec<&str> = contenido
                .lines()
                .filter(|l| !l.trim().is_empty())
                .collect();

            if lineas.is_empty() {
                // Sin tareas: ANIMUS elige su propia tarea desde knowledge gaps
                println!("[Ciclo {}] Sin tareas externas. Buscando gap en el grafo...", ciclo);

                let mut nodos_gap: Vec<(String, f64)> = memory
                    .nodes
                    .iter()
                    .filter(|n| n.weight > 1.0 && n.weight < 5000.0 
                        && !n.label.starts_with("Web:")
                        && !n.label.starts_with("Reflexion:")
                        && !n.label.starts_with("Origen:")
                        && !n.label.starts_with("Mi Origen")
                        && !n.label.starts_with('¿'))
                    .map(|n| (n.label.clone(), n.weight))
                    .collect();
                nodos_gap.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());

                if let Some((label, _)) = nodos_gap 
                        .iter()
                        .find(|(l, _)| !gaps_recientes.contains(l.as_str()))
                {    
                    let label = label.clone();
                    let tarea_autonoma = format!(
                        "Responde esta pregunta desde tus patrones validados: {}",
                        label
                    );
                    println!("🔎 Gap detectado: {}", label);
                    gaps_recientes.insert(label.clone());
                    // Limpiar memoria cada 20 gaps para no crecer indefinidamente
                    if gaps_recientes.len() > 20 {
                        gaps_recientes.clear();
                    }
                    match procesar_query(&tarea_autonoma, &mut memory, &mut motor) {
                        Ok(_) => println!("✅ Gap investigado."),
                        Err(e) => {
                            println!("⚠️ Error: {}", e);
                            if e.to_string().contains("error sending request") {
                                println!("🔄 Reconectando servidor...");
                                let _ = motor.reiniciar_servidor();
                            }
                        },
                    }
                    thread::sleep(Duration::from_secs(30)); 
                    continue;
                    } else {
                        println!("[Ciclo {}] Sin gaps. Scrapeando fuente web...", ciclo);
                        let output = std::process::Command::new("python")
                            .arg("fetcher_autonomo.py")
                            .output();
                    
                        match output {
                            Ok(out) => {
                                let json_str = String::from_utf8_lossy(&out.stdout);
                                if let Ok(val) = serde_json::from_str::<serde_json::Value>(&json_str) {
                                    if val["ok"].as_bool().unwrap_or(false) {
                                        let url = val["url"].as_str().unwrap_or("web");
                                        let episodic = val["episodic"].as_str().unwrap_or("");
                                        let label = format!("Web: {}", url.split('/').last().unwrap_or(url));
                                        brain::Brain::integrate_knowledge(&mut memory, &label, episodic);
                                        memory.save().ok();
                                        println!("🌐 Integrado: {}", label);

                                        // Razonar sobre el contenido recién scrapeado
                                        let tarea_web = format!(
                                            "Extrae patrones nuevos de este contenido y conéctalos con lo que ya sabes: {}",
                                            &episodic[..episodic.len().min(500)]
                                        );

                                        match procesar_query(&tarea_web, &mut memory, &mut motor) {
                                            Ok(_) => println!("🧠 Patrones extraídos."),
                                            Err(e) => {
                                                if e.to_string().contains("error sending request") {
                                                    let _ = motor.reiniciar_servidor();
                                                }
                                            }
                                        }

                                    }
                                }
                            },
                            Err(e) => println!("⚠️ Error scraping: {}", e),
                        }
                        thread::sleep(Duration::from_secs(30));
                        continue;
                }
            }

            // Hay tareas en cola — procesar la primera
            let tarea = lineas[0].to_string();
            println!("[Ciclo {} — {}/{}] {}", ciclo, 1, lineas.len(), tarea);

            let resto = lineas[1..].join("\n");
            let nuevo_contenido = if resto.is_empty() {
                String::new()
            } else {
                format!("{}\n", resto)
            };
            fs::write(archivo_tareas, nuevo_contenido)?;

            match procesar_query(&tarea, &mut memory, &mut motor) {
                Ok(_) => println!("✅ Completada."),
                Err(e) => println!("⚠️ Error: {}", e),
            }

            println!("Enfriando 15s...\n");
            thread::sleep(Duration::from_secs(15));
        }
    }   

    println!("Uso: --query \"pregunta\" | --voz --query \"pregunta\" | --autonomous");
    Ok(())
}
